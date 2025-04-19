from flask import Flask, Response, request, jsonify
from flask_cors import CORS
from flask_migrate import Migrate
from models import db, User, Feed
from routes import init_routes
from config import Config
import jwt
import cv2
from ultralytics import YOLO
import logging
import time
from utils.fcm import send_push_notification  # ✅ Use HTTP v1 version here

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Flask App Setup
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)
init_routes(app)

# 🔥 YOLO + RTSP Camera Stream
class Camera:
    def __init__(self, rtsp_url, user):
        self.rtsp_url = rtsp_url
        self.model = YOLO('../yolo_models/best_nano_111.pt')
        self.cap = cv2.VideoCapture(rtsp_url)
        self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
        self.last_detect = 0
        self.last_results = []
        self.user = user
        self.fire_notified = False

    def get_annotated_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None

        frame = cv2.resize(frame, (480, 272))

        try:
            now = time.time()
            if now - self.last_detect > 2:
                self.last_detect = now
                self.last_results = self.model(frame)

                for result in self.last_results:
                    for box in result.boxes:
                        cls = int(box.cls[0])
                        label = result.names[cls]
                        print(f"this is {label}")

                        if label.lower() == "fire":
                            print("🔥 FIRE DETECTED!")
                            self.fire_notified = True
                            if self.user.fcm_token:
                                send_push_notification(
                                    self.user.fcm_token,
                                    "🔥 Fire Alert",
                                    f"Fire detected in feed: {self.rtsp_url}"
                                )
                                print("Push notification sent to user.")

            for result in self.last_results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    conf = box.conf[0]
                    label = f"{result.names[int(box.cls[0])]} {conf:.2f}"
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, label, (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        except Exception as e:
            logger.error(f"Detection failed: {e}")

        return frame

    def release(self):
        if self.cap:
            self.cap.release()

# ✅ Token saving route (from Flutter HomePage)
@app.route('/api/register_fcm', methods=['POST'])
def save_fcm_token():
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    if not token:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return jsonify({"error": "Invalid token"}), 403

    user = db.session.get(User, payload['user_id'])
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    fcm_token = data.get('fcmToken')

    if not fcm_token:
        return jsonify({"error": "FCM token missing"}), 400

    user.fcm_token = fcm_token
    db.session.commit()
    return jsonify({"message": "Token saved successfully"}), 200

@app.route('/mjpeg/<int:feed_id>')
def mjpeg_stream(feed_id):
    token = request.args.get('token')
    if not token:
        return "Unauthorized", 401

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
    except jwt.InvalidTokenError:
        return "Invalid token", 403

    with app.app_context():
        user = db.session.get(User, payload['user_id'])
        if not user:
            return "User not found", 404
        feed = Feed.query.filter_by(id=feed_id, user_id=user.id).first()
        if not feed or not feed.rtsp_url:
            return "Feed not found", 404

    camera = Camera(feed.rtsp_url, user)

    def generate():
        while True:
            frame = camera.get_annotated_frame()
            if frame is None:
                continue
            ret, jpeg = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 50])
            if not ret:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + jpeg.tobytes() + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
