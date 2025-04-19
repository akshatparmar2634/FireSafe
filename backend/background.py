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
        self.model = YOLO('../yolo_models/best_nano_111.pt')
        self.running = True
        self.fire_notified = False
        self.last_notification_time = 0
        self.notification_cooldown = 2
        
    def run_detection(self):
        """Single thread handling camera, detection and notification"""
        cap = None
        reconnect_attempts = 0
        fire_start_time = 0
        
        while self.running:
            try:
                # Connect to camera if needed
                if cap is None or not cap.isOpened():
                    logger.info(f"Connecting to stream: {self.rtsp_url}")
                    
                    # For RTSP streams, use a modified URL with UDP transport
                    connection_url = self.rtsp_url
                    if self.rtsp_url.startswith("rtsp://"):
                        # Try to add transport protocol - this is more compatible than using cv2.CAP_PROP_RTSP_TRANSPORT
                        if "?" not in connection_url:
                            connection_url += "?transport=udp"
                        elif "&transport=" not in connection_url and "transport=" not in connection_url:
                            connection_url += "&transport=udp"
                    
                    # Open with minimal buffering
                    cap = cv2.VideoCapture(connection_url)
                    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
                    
                    if not cap.isOpened():
                        reconnect_attempts += 1
                        logger.warning(f"Failed to connect to {self.rtsp_url} (attempt {reconnect_attempts})")
                        time.sleep(min(reconnect_attempts, 5))  # Backoff strategy
                        continue
                    reconnect_attempts = 0
                
                # Read frame
                ret, frame = cap.read()
                if not ret:
                    logger.warning(f"Failed to read frame from {self.rtsp_url}")
                    cap.release()
                    cap = None
                    continue
                
                # Process frame
                frame = cv2.resize(frame, (480, 272))
                results = self.model(frame)
                
                # Check for fire
                fire_detected = False
                confidence = 0.0
                
                for result in results:
                    for box in result.boxes:
                        if box.conf[0] > 0.6:
                            cls = int(box.cls[0])
                            label = result.names[cls]
                            if label.lower() == "fire":
                                fire_detected = True
                                confidence = float(box.conf[0])
                                break
                    if fire_detected:
                        break
                
                current_time = time.time()
                
                # Handle fire detection
                if fire_detected:
                    # Start timing for confirmation
                    if fire_start_time == 0:
                        fire_start_time = current_time
                        logger.info(f"🔥 Potential fire detected in feed: {self.rtsp_url} (confidence: {confidence:.2f})")
                    
                    # Only notify if fire has been consistently detected for a short period (reduces false alarms)
                    if current_time - fire_start_time > 0.05:  # 200ms confirmation time
                        # Check if we can send notification (not recently sent)
                        if not self.fire_notified and current_time - self.last_notification_time > self.notification_cooldown:
                            if self.user.fcm_token:
                                try:
                                    logger.info(f"Sending immediate fire notification to user {self.user.id}")
                                    send_push_notification(
                                        self.user.fcm_token,
                                        "🔥 Fire Alert",
                                        f"Fire detected in feed: {self.feed.name or self.rtsp_url} (confidence: {confidence:.2f})"
                                    )
                                    self.fire_notified = True
                                    self.last_notification_time = current_time
                                except Exception as e:
                                    logger.error(f"Failed to send notification: {e}")
                else:
                    # Reset fire detection if no fire is detected
                    fire_start_time = 0
                    
                    # Reset notification flag after a minute of no fire
                    if self.fire_notified and current_time - self.last_notification_time > 5:
                        self.fire_notified = False
                
            except Exception as e:
                logger.error(f"Detection error for {self.rtsp_url}: {e}")
                if cap:
                    cap.release()
                    cap = None
                time.sleep(1)
        
        # Cleanup
        if cap:
            cap.release()
        logger.info(f"Detection thread stopped for {self.rtsp_url}")

    def start(self):
        """Start the detector thread"""
        self.thread = threading.Thread(target=self.run_detection)
        self.thread.daemon = True
        self.thread.start()
        logger.info(f"Started detector for {self.rtsp_url}")
        
    def stop(self):
        """Stop the detector thread"""
        self.running = False
        logger.info(f"Stopping detector for {self.rtsp_url}")


def monitor_feeds():
    active_detectors = {}
    
    with app.app_context():
        while True:
            try:
                feeds = Feed.query.all()
                current_feed_ids = set()
                
                # Start detectors for new or existing feeds
                for feed in feeds:
                    current_feed_ids.add(feed.id)
                    user = db.session.get(User, feed.user_id)
                    
                    if not user or not feed.rtsp_url:
                        continue
                        
                    # Check if detector already exists for this feed
                    if feed.id not in active_detectors:
                        detector = FireDetector(feed, user)
                        detector.start()
                        active_detectors[feed.id] = detector
                
                # Stop and remove detectors for feeds that no longer exist
                feeds_to_remove = []
                for feed_id in active_detectors:
                    if feed_id not in current_feed_ids:
                        active_detectors[feed_id].stop()
                        feeds_to_remove.append(feed_id)
                        
                for feed_id in feeds_to_remove:
                    del active_detectors[feed_id]
                    
                # Sleep before next refresh
                time.sleep(60) 
                
            except Exception as e:
                logger.error(f"Error in monitor_feeds: {e}")
                time.sleep(60)  # Wait before restarting

if __name__ == '__main__':
    logger.info("Starting compatible fire notification service...")
    monitor_feeds()