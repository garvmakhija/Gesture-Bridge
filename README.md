# Gesture Bridge

A real-time hand gesture detection and event delivery system built with Python, MediaPipe, Streamlit, WebRTC and asynchronous webhooks.

Gesture Bridge captures live camera frames, extracts hand landmarks, classifies predefined gestures using geometric rules, stabilizes predictions across multiple frames, and optionally sends stable gesture events to an HTTP webhook.

## Features

- Real-time webcam-based hand gesture detection
- MediaPipe hand landmark extraction
- Six supported gestures
- Landmark-based geometric gesture classification
- Temporal gesture stabilization
- Event cooldown to reduce repeated triggers
- Asynchronous webhook delivery
- Background webhook worker
- Bounded event queue
- Webhook delivery history
- Delivery success and failure tracking
- Real-time FPS monitoring
- Frame processing latency monitoring
- Webhook latency monitoring
- Docker support
- Lightweight local webhook receiver

## Supported Gestures

| Gesture | Description |
|---|---|
| THUMBS UP | Thumb extended upward with other fingers curled |
| THUMBS DOWN | Thumb extended downward with other fingers curled |
| OPEN PALM | Four fingers extended |
| FIST | Four fingers curled |
| VICTORY | Index and middle fingers extended |
| POINT UP | Only index finger extended |

