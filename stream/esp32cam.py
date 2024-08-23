"""
ESP32-CAM Streaming via Flask

Streams video from an ESP32-CAM, fetching the URL from the 'ESP32_CAM_URL'
Linux environment variable.

Dependencies: Flask, OpenCV
"""

import os
import cv2
from flask import Flask, Response, request
from ntfy import send_warning

# Retrieve the ESP32-CAM URL from the Linux environment variable
esp32_cam_url = os.getenv('ESP32_IP')

# Alternatively, set the correct URL if the environment variable is not set
# esp32_cam_url = 'http://192.168.1.193:81/stream'

app = Flask(__name__)

def generate_frames():
    """Open the video stream and yield frames for streaming."""
    cap = cv2.VideoCapture(esp32_cam_url.strip('"'))  # pylint: disable=E1101

    if not cap.isOpened():
        print(f"Error: Could not open video stream from {esp32_cam_url}.")
        return

    while True:
        success, frame = cap.read()

        if not success:
            break

        # Encode the frame in JPEG format
        _, buffer = cv2.imencode('.jpg', frame)  # pylint: disable=E1101
        frame = buffer.tobytes()

        # Yield the frame in the correct format for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/stream')
def video_feed():
    """Video streaming route for the ESP32-CAM feed."""
    client_ip = request.remote_addr
    print(f"Request received from IP address: {client_ip}")
    send_warning(f"Web cam access from IP address: {client_ip}")
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    print(f"ESP32-CAM URL from environment: {esp32_cam_url}")  # For testing purposes
    app.run(host='0.0.0.0', port=8090)
