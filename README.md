# FireSafe: Real-Time Fire and Person Detection with Automated Notification Alerting Using CCTV Surveillance Footage

## Overview

**FireSafe** is a real-time mobile-first safety solution that detects fire and persons using live CCTV feeds. It leverages the lightweight **[YOLOv11n](https://docs.ultralytics.com/models/yolo11/)** deep learning model trained on the [D-Fire](https://www.kaggle.com/datasets/shubhamkarande13/d-fire) and [Human](https://www.kaggle.com/datasets/fareselmenshawii/human-dataset) datasets to provide efficient, accurate detections. When a fire or person is detected, users are instantly notified via mobile alerts and audible device beeps. The end-to-end pipeline consists of:

- A **Flutter-based mobile app** for viewing live feeds and alerts
- A **Flask backend** that processes CCTV RTSP streams in real-time
- **Firebase Cloud Messaging (FCM)** for sending notifications

### 📱 Demo

<video src="demo/Mobile App Demo.mp4" controls width="600"></video>

## Features

- Live multi-camera feed monitoring
- Real-time fire and person detection
- Alert notifications via Firebase
- Secure user authentication and feed management
- Annotated live stream using MJPEG rendering

## Directory Structure

```
FireSafe/
├── backend/                # Flask backend for inference and streaming
│   ├── app.py              # Main app with routes for inference
│   ├── background.py       # Background thread for stream processing
│   ├── model/              # Trained YOLOv11n weights and inference utils
│   └── requirements.txt    # Python dependencies
├── frontend/               # Flutter mobile app
│   ├── lib/                # Dart source code
│   ├── pubspec.yaml        # Flutter dependencies
├── README.md               # Project documentation
└── demo/                   # Sample videos, screenshots, and results
```

## Installation

### Frontend

1. Install [Flutter SDK](https://docs.flutter.dev/get-started/install).
2. Connect a device or emulator.
3. Navigate to the frontend folder and run:

```bash
cd frontend/
flutter clean
flutter pub get
flutter run
```

### Backend

1. Ensure Python 3.8+ is installed.
2. Create a virtual environment (optional but recommended).
3. Install backend dependencies and start the server:

```bash
cd backend/
pip install -r requirements.txt
python app.py
python background.py
```

> Note: Inference runs on YOLOv11n using the Tapo TP-Link C212 camera RTSP stream.

## How to Run

1. Launch the backend server first (`app.py` and `background.py`).
2. Start the frontend Flutter app on your mobile device.
3. Log in, add camera feeds, and view live detections in real-time.
4. Notifications are automatically pushed when fire/person is detected with confidence above the set threshold.

## Model Details

| Model       | mAP@0.5 | mAP@0.5:0.95 | Latency |
|-------------|---------|--------------|---------|
| YOLOv8n     | 0.743   | 0.426        | 61 ms   |
| RTMDet-tiny | 0.754   | 0.435        | 57 ms   |
| **YOLOv11n** | **0.768** | **0.446**    | **54 ms** |

YOLOv11n outperformed all baselines in both detection accuracy and latency, making it ideal for real-time mobile deployment.

## Datasets Used

- **[D-Fire Dataset](https://github.com/gaiasd/DFireDataset)** — Annotated real-world CCTV fire images
- **[Human Dataset](https://www.kaggle.com/datasets/fareselmenshawii/human-dataset)** — Person detection under diverse indoor and outdoor scenes

## Complete Demo

You can Watch our complete system in action: [Demo Video on Google Drive](https://drive.google.com/drive/folders/1Ah_3Q2hE8MIuD93e6HLDXtjwC_hqN0H_?usp=sharing)