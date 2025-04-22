import torch
import threading
import time
import cv2
from ultralytics import YOLO
from models import db, Feed, User
from config import Config
from utils.fcm import send_push_notification
import logging
from flask import Flask

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask app for database configuration
app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

class FireDetector:
    def __init__(self, feed, user):
        self.feed = feed
        self.user = user
        self.rtsp_url = feed.rtsp_url
        # Check if CUDA is available
        self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        logger.info(f"Using device: {self.device}")

        # Load models and move them to the appropriate device
        self.fire_model = YOLO('../detection_models/yolo_models/baseline_11.pt')
        self.fire_model.to(self.device)  # Move the fire model to the specified device

        self.person_model = YOLO('../detection_models/yolo_models/baseline_11_p.pt')
        self.person_model.to(self.device)  # Move the person model to the specified device
        
        self.running = True
        self.fire_notified = False
        self.person_notified = False
        self.last_notification_time = 0
        self.notification_cooldown = 2

        self.post_fire_monitoring = False
        self.post_fire_start_time = 0

    def detect_fire(self, frame):
        results = self.fire_model(frame)
        for result in results:
            for box in result.boxes:
                if box.conf[0] > 0.65:
                    cls = int(box.cls[0])
                    label = result.names[cls]
                    if label.lower() == "fire":
                        return True, float(box.conf[0])
        return False, 0.0

    def detect_person(self, frame):
        results = self.person_model(frame)
        for result in results:
            for box in result.boxes:
                if box.conf[0] > 0.65:
                    cls = int(box.cls[0])
                    label = result.names[cls]
                    if label.lower() == "person":
                        return True
        return False

    def run_detection(self):
        cap = None
        reconnect_attempts = 0
        fire_start_time = 0

        while self.running:
            try:
                if cap is None or not cap.isOpened():
                    logger.info(f"Connecting to stream: {self.rtsp_url}")
                    connection_url = self.rtsp_url
                    if self.rtsp_url.startswith("rtsp://"):
                        if "?" not in connection_url:
                            connection_url += "?transport=udp"
                        elif "&transport=" not in connection_url and "transport=" not in connection_url:
                            connection_url += "&transport=udp"
                    cap = cv2.VideoCapture(connection_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)

                    if not cap.isOpened():
                        reconnect_attempts += 1
                        logger.warning(f"Failed to connect to {self.rtsp_url} (attempt {reconnect_attempts})")
                        time.sleep(min(reconnect_attempts, 5))
                        continue
                    reconnect_attempts = 0

                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from {self.rtsp_url}")
                    cap.release()
                    cap = None
                    continue

                frame = cv2.resize(frame, (480, 272))
                fire_detected, confidence = self.detect_fire(frame)
                current_time = time.time()

                if fire_detected:
                    if fire_start_time == 0:
                        fire_start_time = current_time
                        logger.info(f"🔥 Potential fire detected in feed: {self.rtsp_url} (confidence: {confidence:.2f})")

                    if current_time - fire_start_time > 1:
                        if not self.fire_notified and current_time - self.last_notification_time > self.notification_cooldown:
                            if self.user.fcm_token:
                                try:
                                    logger.info(f"Sending fire notification to user {self.user.id}")
                                    send_push_notification(
                                        self.user.fcm_token,
                                        "🔥 Fire Alert",
                                        f"Fire detected in feed: {self.feed.name or self.rtsp_url} (confidence: {confidence:.2f})"
                                    )
                                    self.fire_notified = True
                                    self.last_notification_time = current_time
                                    self.post_fire_monitoring = True
                                    self.post_fire_start_time = current_time
                                    self.person_notified = False
                                except Exception as e:
                                    logger.error(f"Failed to send fire notification: {e}")
                else:
                    fire_start_time = 0
                    if self.fire_notified and current_time - self.last_notification_time > 5:
                        self.fire_notified = False

                if self.post_fire_monitoring:
                    if current_time - self.post_fire_start_time < 10:
                        person_found = self.detect_person(frame)
                        if person_found and not self.person_notified:
                            logger.info(f"👤 Person detected post-fire in feed {self.rtsp_url}")
                            send_push_notification(
                                self.user.fcm_token,
                                "🚨 Person Detected",
                                f"Person seen in camera after fire alert: {self.feed.name or self.rtsp_url}"
                            )
                            self.person_notified = True
                    else:
                        self.post_fire_monitoring = False

            except Exception as e:
                logger.error(f"Detection error for {self.rtsp_url}: {e}")
                if cap:
                    cap.release()
                    cap = None
                time.sleep(1)

        if cap:
            cap.release()
        logger.info(f"Detection thread stopped for {self.rtsp_url}")

    def start(self):
        self.thread = threading.Thread(target=self.run_detection)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started detector for {self.rtsp_url}")

    def stop(self):
        self.running = False
        logger.info(f"Stopping detector for {self.rtsp_url}")


def monitor_feeds():
    active_detectors = {}

    with app.app_context():
        while True:
            try:
                feeds = Feed.query.all()
                current_feed_ids = set()

                for feed in feeds:
                    current_feed_ids.add(feed.id)
                    user = db.session.get(User, feed.user_id)

                    if not user or not feed.rtsp_url:
                        continue

                    if feed.id not in active_detectors:
                        detector = FireDetector(feed, user)
                        detector.start()
                        active_detectors[feed.id] = detector

                feeds_to_remove = []
                for feed_id in active_detectors:
                    if feed_id not in current_feed_ids:
                        active_detectors[feed_id].stop()
                        feeds_to_remove.append(feed_id)

                for feed_id in feeds_to_remove:
                    del active_detectors[feed_id]

                time.sleep(60)

            except Exception as e:
                logger.error(f"Error in monitor_feeds: {e}")
                time.sleep(60)

if __name__ == '__main__':
    logger.info("Starting fire and person monitoring service...")
    monitor_feeds()


