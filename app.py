import av
import cv2
import threading
import time
import streamlit as st
from streamlit_webrtc import webrtc_streamer, WebRtcMode
# My Modules
from src.gesture_detector import GestureDetector
from src.gesture_engine import GestureEngine
from src.gesture_stabilizer import GestureStabilizer
from src.webhook import WebhookDispatcher


st.set_page_config(
    page_title="Gesture Bridge",
    page_icon="✋",
    layout="wide"
)


class RuntimeConfig:
    def __init__(self):
        self.webhook_url = ""
        self.webhook_enabled = False
        self.lock = threading.Lock()
    def update(self, url, enabled):
        with self.lock:
            self.webhook_url = url
            self.webhook_enabled = enabled
    def get(self):
        with self.lock:
            return self.webhook_url, self.webhook_enabled

class PerformanceStats:
    def __init__(self):
        self.lock = threading.Lock()
        self.frame_times = []
        self.fps = 0.0
        self.processing_latency = 0.0

    def update(self, latency):
        with self.lock:
            self.processing_latency = latency
            self.frame_times.append(time.perf_counter())

            if len(self.frame_times) > 30:
                self.frame_times.pop(0)

            if len(self.frame_times) >= 2:
                elapsed = (
                    self.frame_times[-1]
                    - self.frame_times[0]
                )

                if elapsed > 0:
                    self.fps = (
                        len(self.frame_times) - 1
                    ) / elapsed
    def get(self):
        with self.lock:
            return {
                "fps": self.fps,
                "latency": self.processing_latency
            }

@st.cache_resource
def get_runtime():
    return RuntimeConfig()

@st.cache_resource
def get_performance():
    return PerformanceStats()


@st.cache_resource
def get_detector():
    return GestureDetector()


@st.cache_resource
def get_engine():
    return GestureEngine()


@st.cache_resource
def get_stabilizer():
    return GestureStabilizer(
        window_size=5,
        cooldown=0.8
    )


@st.cache_resource
def get_dispatcher():
    return WebhookDispatcher()


runtime = get_runtime()
performance = get_performance()
detector = get_detector()
engine = get_engine()
stabilizer = get_stabilizer()
dispatcher = get_dispatcher()


st.title("Gesture Bridge")
st.caption(
    "Real-Time Hand Gesture Detection & Event Delivery"
)


left, right = st.columns([2.2, 1])


with right:
    st.subheader("Webhook")

    webhook_url = st.text_input(
        "Endpoint URL",
        placeholder="http://host.docker.internal:9000/webhook"
    )

    webhook_enabled = st.toggle(
        "Enable Webhook",
        value=False
    )

    runtime.update(
        webhook_url,
        webhook_enabled
    )

    if webhook_enabled and dispatcher.validate_url(
        webhook_url
    ):
        st.success("Webhook ready")
    elif webhook_enabled:
        st.warning("Enter a valid webhook URL")
    else:
        st.info("Webhook disabled")

    st.divider()

    st.subheader("Supported Gestures")

    st.write("👍 Thumbs Up")
    st.write("👎 Thumbs Down")
    st.write("✋ Open Palm")
    st.write("✊ Fist")
    st.write("✌️ Victory")
    st.write("☝️ Point Up")


def video_frame_callback(frame):
    start_time = time.perf_counter()
    image = frame.to_ndarray(format="bgr24")
    processed_frame, result = detector.process(image)
    gesture = "NO HAND"
    if result.multi_hand_landmarks:
        raw_gesture = engine.detect(
            result.multi_hand_landmarks[0]
        )
        gesture, event = stabilizer.update(
            raw_gesture
        )
        url, enabled = runtime.get()
        if (
            event
            and enabled
            and dispatcher.validate_url(url)
        ):
            dispatcher.submit(
                event,
                url
            )
    else:
        stabilizer.reset()

    processing_time = (
        time.perf_counter() - start_time
    )
    performance.update(processing_time)
    cv2.rectangle(
        processed_frame,
        (20, 20),
        (370, 80),
        (15, 15, 15),
        -1
    )
    cv2.putText(
        processed_frame,
        gesture,
        (35, 60),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.9,
        (255, 255, 255),
        2,
        cv2.LINE_AA
    )

    return av.VideoFrame.from_ndarray(
        processed_frame,
        format="bgr24"
    )


with left:
    st.subheader("Live Detection")

    webrtc_streamer(
        key="gesture-camera",
        mode=WebRtcMode.SENDRECV,
        video_frame_callback=video_frame_callback,
        media_stream_constraints={
            "video": {
                "width": {"ideal": 1280},
                "height": {"ideal": 720},
                "frameRate": {"ideal": 30}
            },
            "audio": False
        },
        async_processing=True
    )


st.divider()


@st.fragment(run_every="1s")
def performance_dashboard():
    st.subheader("Live Performance")
    performance_data = performance.get()
    webhook_data = dispatcher.get_stats()
    metric1, metric2, metric3, metric4 = st.columns(4)

    with metric1:
        st.metric(
            "FPS",
            f"{performance_data['fps']:.1f}"
        )

    with metric2:
        st.metric(
            "Processing",
            f"{performance_data['latency'] * 1000:.1f} ms"
        )

    with metric3:
        st.metric(
            "Webhook",
            f"{webhook_data['last_latency'] * 1000:.1f} ms"
        )

    with metric4:
        st.metric(
            "Queue",
            webhook_data["queue"]
        )

    metric5, metric6, metric7 = st.columns(3)

    with metric5:
        st.metric(
            "Total Events",
            webhook_data["total"]
        )

    with metric6:
        st.metric(
            "Delivered",
            webhook_data["delivered"]
        )

    with metric7:
        st.metric(
            "Failed",
            webhook_data["failed"]
        )


performance_dashboard()

st.divider()

st.subheader("Recent Events")
events = dispatcher.get_history()
if events:
    for event in events[:8]:
        if event["status"] == "DELIVERED":
            icon = "✅"
        else:
            icon = "❌"

        st.write(
            f"{icon} **{event['gesture']}** "
            f"— {event['status']} — {event['timestamp']}"
        )
else:
    st.caption("No webhook events yet.")