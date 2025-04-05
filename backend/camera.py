import cv2
import numpy as np

class Camera:
    def __init__(self, rtsp_url):
        self.rtsp_url = rtsp_url
        self.cap = cv2.VideoCapture(rtsp_url)
        
        if not self.cap.isOpened():
            raise ValueError("Error: Could not open video stream.")

    def get_frame(self):
        success, frame = self.cap.read()
        if not success:
            return None
        ret, buffer = cv2.imencode('.jpg', frame)
        return buffer.tobytes()

    def release(self):
        self.cap.release()

def generate_frames(camera):
    while True:
        frame = camera.get_frame()
        if frame is None:
            break
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')