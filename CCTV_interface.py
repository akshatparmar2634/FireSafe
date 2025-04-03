import numpy as np
from ultralytics import YOLO
import cv2
import os
import torch

# Load the YOLO model
model_path = 'best_nano_111.pt'
model = YOLO(model_path)

# RTSP URL for camera stream
rtsp_url = 'rtsp://akshatparmar2634:cvproject@192.168.137.149:554/stream1'

# Initialize video capture with the RTSP URL
cap = cv2.VideoCapture(rtsp_url)

# Check if the video stream is opened successfully
if not cap.isOpened():
    print("Error: Could not open video stream.")
    exit()

# Loop to continuously capture frames from the video stream
while True:
    ret, frame = cap.read()  # Read the frame from the stream
    if not ret:
        print("Error: Failed to read frame from camera.")
        break
    
    # Run detection on the frame with verbose=False to disable printing
    results = model(frame, verbose=False)
    
    # Check if fire is detected
    if len(results[0].boxes) > 0:
        boxes = results[0].boxes
        for box in boxes:
            # Get the class index
            cls = int(box.cls[0])
            # Get class name from model's class names dictionary
            cls_name = results[0].names[cls]
            
            if cls_name.lower() == "fire":
                # Print detection when fire is found
                confidence = float(box.conf[0])
                print(f"Fire detected with confidence: {confidence:.2f}")
    
    # Visualize the results on the frame
    annotated_frame = results[0].plot()
    
    # Display the annotated frame
    cv2.imshow("Object Detection", annotated_frame)
    
    # Add a key press check to exit the loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break
    
# Release the video capture object and close the window
cap.release()
cv2.destroyAllWindows()
