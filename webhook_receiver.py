from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import time


class WebhookHandler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path != "/webhook":
            self.send_response(404)
            self.end_headers()
            return

        content_length = int(
            self.headers.get("Content-Length", 0)
        )

        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode("utf-8"))

            received_at = time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            )

            print("\n" + "=" * 50)
            print("NEW GESTURE EVENT")
            print("=" * 50)
            print(json.dumps(data, indent=4))
            print(f"Received: {received_at}")
            print("=" * 50)

            response = {
                "status": "received",
                "gesture": data.get("gesture"),
                "received_at": received_at
            }

            response_data = json.dumps(
                response
            ).encode("utf-8")

            self.send_response(200)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.send_header(
                "Content-Length",
                str(len(response_data))
            )
            self.end_headers()
            self.wfile.write(response_data)

        except (json.JSONDecodeError, UnicodeDecodeError):
            self.send_response(400)
            self.send_header(
                "Content-Type",
                "application/json"
            )
            self.end_headers()

            response = {
                "status": "error",
                "message": "Invalid JSON payload"
            }

            self.wfile.write(
                json.dumps(response).encode("utf-8")
            )

    def log_message(self, format, *args):
        return


server = ThreadingHTTPServer(
    ("0.0.0.0", 9000),
    WebhookHandler
)

print("Webhook receiver running...")
print("Endpoint: http://0.0.0.0:9000/webhook")

server.serve_forever()