from flask import Flask, request
from flask_cors import CORS
from flask_migrate import Migrate  
from models import db, User, Feed  # Your existing models
from routes import init_routes
from config import Config
import asyncio
import websockets
from camera import Camera, generate_frames_base64  # Generator yielding base64 strings
import jwt
import threading

app = Flask(__name__)

# Enable CORS for development
CORS(app, resources={
    r"/*": {
        "origins": ["*"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "*"]
    }
})

@app.before_request
def log_request():
    print(f"[REQUEST DEBUG] {request.method} {request.path} Headers: {request.headers}")

app.config.from_object(Config)
db.init_app(app)
migrate = Migrate(app, db)
init_routes(app)

# WebSocket handler.
# The Flutter client must supply the feed ID in the custom header "feed_id".
async def video_feed_websocket(websocket, path):
    # Retrieve feed_id from the custom header; otherwise, parse from the URL.
    feed_id_str = websocket.request_headers.get('feed_id')
    if not feed_id_str:
        try:
            feed_id_str = path.split('/')[-1]
        except Exception:
            await websocket.send("Error: Feed ID not provided")
            await websocket.close()
            return

    try:
        feed_id = int(feed_id_str)
    except ValueError:
        await websocket.send("Error: Feed ID is not an integer")
        await websocket.close()
        return

    print(f"[WS DEBUG] Feed ID extracted: {feed_id}")

    # Retrieve token from the Authorization header.
    token = websocket.request_headers.get('Authorization', '').replace('Bearer ', '')
    print(f"[WS DEBUG] Token received: {token}")
    if not token:
        await websocket.send("Error: No token provided")
        await websocket.close()
        return

    try:
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        print(f"[WS DEBUG] JWT payload: {payload}")
    except jwt.InvalidTokenError as e:
        print(f"[WS DEBUG] Token decode error: {e}")
        await websocket.send("Error: Invalid token")
        await websocket.close()
        return

    # All db queries need an application context.
    with app.app_context():
        current_user = db.session.get(User, payload['user_id'])
    print(f"[WS DEBUG] Current user: {current_user}")
    if not current_user:
        await websocket.send("Error: Invalid token")
        await websocket.close()
        return

    with app.app_context():
        feed = Feed.query.filter_by(id=feed_id, user_id=current_user.id).first()
    print(f"[WS DEBUG] Feed retrieved: {feed}")
    if not feed or not feed.rtsp_url:
        await websocket.send("Error: Feed not found or no RTSP URL configured")
        await websocket.close()
        return

    print(f"[WS DEBUG] Initializing camera with RTSP URL: {feed.rtsp_url}")
    camera = Camera(feed.rtsp_url)
    print("[WS DEBUG] Camera initialized, starting frame generation")
    try:
        for frame in generate_frames_base64(camera):  # frame is a base64-encoded string
            print(f"[WS DEBUG] Sending frame (base64 length: {len(frame)} characters)")
            await websocket.send(frame)
            await asyncio.sleep(0.033)  # ~30 fps
    except websockets.ConnectionClosed:
        print(f"[WS DEBUG] WebSocket connection closed for feed {feed_id}")
    except Exception as ex:
        print(f"[WS DEBUG] Error during frame sending: {ex}")
    finally:
        camera.release()

async def start_websocket_server():
    async with websockets.serve(
        video_feed_websocket,
        "0.0.0.0",
        8765
    ):
        print("[WS DEBUG] WebSocket server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

def run_flask():
    app.run(debug=True, host='0.0.0.0', port=5001, use_reloader=False)

async def main():
    with app.app_context():
        print("[DB DEBUG] Creating database tables...")
        try:
            db.create_all()
            print("[DB DEBUG] Tables created successfully!")
        except Exception as e:
            print(f"[DB DEBUG] Database error: {e}")
            return

    print("[WS DEBUG] Starting WebSocket server...")
    websocket_task = asyncio.create_task(start_websocket_server())
    print("[WS DEBUG] Starting Flask in a separate thread...")
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    try:
        await websocket_task
    except asyncio.CancelledError:
        print("[WS DEBUG] WebSocket server stopped")

if __name__ == '__main__':
    asyncio.run(main())
