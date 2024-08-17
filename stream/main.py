import cv2
from flask import Flask, Response

app = Flask(__name__)

# Open the video capture from the device
cap = cv2.VideoCapture('/dev/video0')

def generate_frames():
    while True:
        # Read a frame from the capture
        success, frame = cap.read()
        if not success:
            break

        # Encode the frame in JPEG format
        ret, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()

        # Yield the frame in the correct format for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8088)