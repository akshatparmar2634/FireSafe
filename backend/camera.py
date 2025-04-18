
# import cv2
# import time
# from ultralytics import YOLO
# import logging

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
# logger = logging.getLogger(__name__)

# class Camera:
#     def __init__(self, rtsp_url):
#         self.rtsp_url = rtsp_url
#         self.cap = None
#         self.model = YOLO('../yolo_models/best_nano_111.pt')  # Adjust model path if needed
#         self._connect()

#     def _connect(self):
#         if self.cap is not None:
#             self.cap.release()
#         self.cap = cv2.VideoCapture(self.rtsp_url)
#         if not self.cap.isOpened():
#             logger.error(f"Failed to open RTSP stream: {self.rtsp_url}")
#         else:
#             logger.info(f"Successfully connected to RTSP stream: {self.rtsp_url}")

#     def get_frame(self):
#         if self.cap is None or not self.cap.isOpened():
#             logger.warning("Capture object not open, attempting to reconnect")
#             self._connect()
#             time.sleep(1)
#             if not self.cap.isOpened():
#                 return None

#         success, frame = self.cap.read()
#         if not success:
#             logger.warning("Failed to read frame, attempting to reconnect")
#             self._connect()
#             return None

#         frame_with_boxes = self._process_frame_with_bounding_boxes(frame)
#         ret, buffer = cv2.imencode('.jpg', frame_with_boxes, [int(cv2.IMWRITE_JPEG_QUALITY), 40])
#         if not ret:
#             logger.error("Failed to encode frame to JPEG")
#             return None
#         return buffer.tobytes()  # ✔ Now returning raw JPEG bytes (not base64)

#     def _process_frame_with_bounding_boxes(self, frame):
#         try:
#             results = self.model(frame)
#             for result in results:
#                 boxes = result.boxes
#                 for box in boxes:
#                     x1, y1, x2, y2 = map(int, box.xyxy[0])
#                     confidence = box.conf[0]
#                     label = f"{result.names[int(box.cls[0])]} {confidence:.2f}"
#                     cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
#                     cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
#             return frame
#         except Exception as e:
#             logger.error(f"Error processing frame with ML model: {e}")
#             return frame

#     def release(self):
#         if self.cap is not None:
#             self.cap.release()
#             logger.info("Released video capture object")