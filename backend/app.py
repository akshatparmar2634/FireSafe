from flask import Flask, Response, render_template
from camera import Camera, generate_frames
import os

app = Flask(__name__)
rtsp_url = os.getenv('RTSP_URL')
camera = Camera(rtsp_url)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    print(camera)
    return Response(generate_frames(camera),
                   mimetype='multipart/x-mixed-replace; boundary=frame')

def cleanup():
    if camera:
        camera.release()

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    except Exception as e:
        print(f"Error: {e}")
    finally:
        cleanup()