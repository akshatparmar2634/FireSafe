
import cv2

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

    # Process the frame (for example, displaying it)
    cv2.imshow("Camera Stream", frame)

    # Exit the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close the window
cap.release()
cv2.destroyAllWindows()
