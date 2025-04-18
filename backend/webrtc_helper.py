# webrtc_helper.py
from aiortc import VideoStreamTrack
from av import VideoFrame
import time
import asyncio

class MLVideoStreamTrack(VideoStreamTrack):
    """
    A custom VideoStreamTrack that pulls frames from your Camera.
    """
    def __init__(self, camera):
        super().__init__()
        self.camera = camera
        self.last_frame_time = None

    async def recv(self):
        # Wait for the next frame – try to obtain a raw frame.
        frame = None
        while frame is None:
            frame = self.camera.get_raw_frame()
            await asyncio.sleep(0.001)  # Yield event loop briefly
        # Convert the raw NumPy frame (assumed BGR) to an AV VideoFrame.
        video_frame = VideoFrame.from_ndarray(frame, format="bgr24")
        now = time.time()
        if self.last_frame_time is None:
            self.last_frame_time = now
        video_frame.pts = int(now * 90000)
        video_frame.time_base = 1 / 90000
        self.last_frame_time = now
        return video_frame
