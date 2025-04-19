# webrtc_server.py
import asyncio
from flask import Flask
from flask_socketio import SocketIO, emit
from aiortc import RTCPeerConnection, RTCSessionDescription
from webrtc_helper import MLVideoStreamTrack
from camera import Camera
from models import db, Feed, User
from config import Config
import jwt

app = Flask(__name__)
app.config.from_object(Config)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode="threading")

def get_feed_camera_url(feed_id, user_id):
    with app.app_context():
        feed = Feed.query.filter_by(id=feed_id, user_id=user_id).first()
        if feed and feed.rtsp_url:
            return feed.rtsp_url
    return None

@socketio.on('offer')
def handle_offer(data):
    """
    Expects:
      {
         'feed_id': '<feed_id>',
         'token': '<JWT token>',
         'sdp': '<offer sdp>'
      }
    """
    print("[SIGNALING] Received offer:", data)
    try:
        feed_id = int(data['feed_id'])
        token = data['token']
        sdp = data['sdp']
    except Exception as e:
        emit('error', {'error': 'Invalid data format'})
        return

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        user_id = payload['user_id']
    except Exception as e:
        emit('error', {'error': 'Invalid token'})
        return

    camera_url = get_feed_camera_url(feed_id, user_id)
    if not camera_url:
        emit('error', {'error': 'Feed not found or RTSP URL missing'})
        return

    pc = RTCPeerConnection()
    print(f"[SIGNALING] Created PeerConnection for feed {feed_id}")

    camera = Camera(camera_url)
    local_video = MLVideoStreamTrack(camera)
    pc.addTrack(local_video)

    async def run_offer():
        await pc.setRemoteDescription(RTCSessionDescription(sdp, 'offer'))
        answer = await pc.createAnswer()
        await pc.setLocalDescription(answer)
        emit('answer', {'sdp': pc.localDescription.sdp, 'type': pc.localDescription.type})
        print("[SIGNALING] Sent answer for feed", feed_id)

    asyncio.run_coroutine_threadsafe(run_offer(), asyncio.get_event_loop())

@socketio.on('candidate')
def handle_candidate(data):
    # Optionally implement ICE candidate handling.
    print("[SIGNALING] Candidate received:", data)
    # For this minimal example, we are not forwarding ICE candidates.

@app.route('/')
def index():
    return "WebRTC Signaling Server Running"

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5002)
