import queue
import threading
import time
from collections import deque
from urllib.parse import urlparse

import requests


class WebhookDispatcher:
    def __init__(self, max_history=30):
        self.events = queue.Queue(maxsize=50)
        self.history = deque(maxlen=max_history)
        self.lock = threading.Lock()

        self.total_events = 0
        self.delivered_events = 0
        self.failed_events = 0
        self.total_latency = 0.0
        self.last_latency = 0.0

        self.worker = threading.Thread(
            target=self._worker,
            daemon=True
        )
        self.worker.start()

    def validate_url(self, url):
        try:
            parsed = urlparse(url)

            return parsed.scheme in {
                "http",
                "https"
            } and bool(parsed.netloc)

        except Exception:
            return False

    def submit(self, gesture, url):
        if not url or not self.validate_url(url):
            return False

        event = {
            "gesture": gesture,
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S"
            ),
            "status": "QUEUED"
        }

        try:
            self.events.put_nowait((event, url))
            return True

        except queue.Full:
            return False

    def get_history(self):
        with self.lock:
            return list(self.history)

    def get_stats(self):
        with self.lock:
            average_latency = (
                self.total_latency / self.delivered_events
                if self.delivered_events
                else 0.0
            )

            return {
                "total": self.total_events,
                "delivered": self.delivered_events,
                "failed": self.failed_events,
                "queue": self.events.qsize(),
                "average_latency": average_latency,
                "last_latency": self.last_latency
            }

    def _worker(self):
        while True:
            event, url = self.events.get()

            start_time = time.perf_counter()

            try:
                response = requests.post(
                    url,
                    json={
                        "gesture": event["gesture"],
                        "timestamp": event["timestamp"]
                    },
                    timeout=3
                )

                latency = time.perf_counter() - start_time

                with self.lock:
                    self.total_events += 1
                    self.last_latency = latency
                    self.total_latency += latency

                if 200 <= response.status_code < 300:
                    event["status"] = "DELIVERED"

                    with self.lock:
                        self.delivered_events += 1
                else:
                    event["status"] = "FAILED"

                    with self.lock:
                        self.failed_events += 1

            except requests.RequestException:
                with self.lock:
                    self.total_events += 1
                    self.failed_events += 1
                    self.last_latency = time.perf_counter() - start_time

                event["status"] = "FAILED"

            finally:
                with self.lock:
                    self.history.appendleft(event)

                self.events.task_done()