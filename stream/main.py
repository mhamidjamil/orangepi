"""Script to broadcast usb camera stream"""
import threading
import atexit
import time
import cv2
from flask import Flask, Response

app = Flask(__name__)

# Global variables to manage the camera and inactivity timeout
CLEAN_UP_TIME = 5
CAP = None
LAST_ACCESS_TIME = time.time()
lock = threading.Lock()

def start_camera():
    """Starts the camera capture."""
    global CAP # pylint: disable=global-statement
    if CAP is None:
        CAP = cv2.VideoCapture('/dev/video0') # pylint: disable=E1101
        if not CAP.isOpened():
            print("Error: Could not open camera.")
            CAP = None

def stop_camera():
    """Releases the camera."""
    global CAP # pylint: disable=global-statement
    if CAP is not None:
        CAP.release()
        CAP = None
        print("Camera stopped and released.")

def check_inactivity():
    """Thread function to check if 30 seconds of inactivity have passed."""
    global LAST_ACCESS_TIME # pylint: disable=global-statement,W0602
    while True:
        time.sleep(1)
        with lock:
            if time.time() - LAST_ACCESS_TIME > CLEAN_UP_TIME and CAP is not None:
                stop_camera()

def generate_frames():
    """Responsable to start stream"""
    global LAST_ACCESS_TIME # pylint: disable=global-statement
    start_camera()  # Start the camera if not started
    while True:
        with lock:
            # Update last access time when frames are requested
            LAST_ACCESS_TIME = time.time()

            if CAP is None:
                break

            # Read a frame from the capture
            success, frame = CAP.read()
            if not success:
                break

            # Encode the frame in JPEG format
            _, buffer = cv2.imencode('.jpg', frame) # pylint: disable=E1101
            frame = buffer.tobytes()

            # Yield the frame in the correct format for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    """Responsable for stream"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

def cleanup():
    """Function to clean up resources when the server shuts down."""
    stop_camera()
    print("Server and camera cleanup completed.")

# Register the cleanup function to run when the app exits
atexit.register(cleanup)

if __name__ == '__main__':
    # Start a thread to check for inactivity
    inactivity_thread = threading.Thread(target=check_inactivity)
    inactivity_thread.daemon = True
    inactivity_thread.start()

    # Run the Flask app
    try:
        app.run(host='0.0.0.0', port=8088, threaded=True)
    except Exception as e: # pylint: disable=broad-except
        print(f"Flask server encountered an error: {e}")
    finally:
        cleanup()
