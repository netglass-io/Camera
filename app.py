"""
Camera Processing Demo - Flask Application
Provides real-time video streaming with face detection and bidirectional communication
"""

from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
import cv2
import time
from datetime import datetime
import os
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'camera-demo-secret'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Global state
camera = None
face_cascade = None
detection_enabled = True
current_fps = 0
last_frame_time = time.time()
frame_count = 0

# Shared metadata for SocketIO emission
metadata_lock = threading.Lock()
latest_metadata = {
    'face_count': 0,
    'faces': [],
    'fps': 0,
    'frame_number': 0,
    'processing_time_ms': 0,
    'detection_time_ms': 0
}

# Configuration from environment variables
CAMERA_DEVICE = int(os.getenv('CAMERA_DEVICE', '/dev/video0').split('video')[-1])
TARGET_FPS = int(os.getenv('TARGET_FPS', '30'))
FRAME_WIDTH = 640
FRAME_HEIGHT = 480


def init_camera():
    """Initialize USB webcam with specified resolution"""
    print(f"Initializing camera at /dev/video{CAMERA_DEVICE}...")
    cap = cv2.VideoCapture(CAMERA_DEVICE)

    if not cap.isOpened():
        raise RuntimeError(f"Failed to open camera at /dev/video{CAMERA_DEVICE}")

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, FRAME_HEIGHT)
    cap.set(cv2.CAP_PROP_FPS, TARGET_FPS)

    # Verify camera is working
    ret, frame = cap.read()
    if not ret:
        raise RuntimeError("Camera opened but failed to read frame")

    print(f"Camera initialized: {FRAME_WIDTH}x{FRAME_HEIGHT} @ {TARGET_FPS} FPS")
    return cap


def init_face_detector():
    """Initialize Haar Cascade face detector"""
    cascade_path = cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    face_cascade = cv2.CascadeClassifier(cascade_path)

    if face_cascade.empty():
        raise RuntimeError("Failed to load Haar Cascade face detector")

    print("Face detector initialized")
    return face_cascade


def metadata_emitter():
    """
    Background thread that emits metadata to connected SocketIO clients
    Runs at ~10Hz to update UI without blocking video stream
    """
    while True:
        time.sleep(0.1)  # 10Hz update rate

        with metadata_lock:
            metadata = latest_metadata.copy()

        # Emit to all connected clients
        socketio.emit('camera_metadata', {
            'face_count': metadata['face_count'],
            'faces': metadata['faces'],
            'fps': metadata['fps'],
            'timestamp': datetime.now().isoformat(),
            'frame_number': metadata['frame_number']
        }, namespace='/')

        socketio.emit('performance_metrics', {
            'processing_time_ms': metadata['processing_time_ms'],
            'detection_time_ms': metadata['detection_time_ms'],
            'fps': metadata['fps']
        }, namespace='/')


def detect_faces(frame):
    """
    Detect faces in frame using Haar cascade
    Returns list of (x, y, w, h) tuples
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
        flags=cv2.CASCADE_SCALE_IMAGE
    )
    return faces


def generate_frames():
    """
    Generator function for MJPEG stream
    Captures frames, performs face detection, and yields JPEG-encoded frames
    """
    global current_fps, last_frame_time, frame_count

    while True:
        frame_start = time.time()

        # Capture frame from camera
        success, frame = camera.read()
        if not success:
            print("Failed to read frame from camera")
            break

        # Perform face detection if enabled
        faces = []
        if detection_enabled:
            detection_start = time.time()
            faces = detect_faces(frame)
            detection_time = (time.time() - detection_start) * 1000

            # Draw bounding boxes on frame
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                # Add label
                cv2.putText(frame, 'Face', (x, y-10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        else:
            detection_time = 0

        # Calculate FPS
        frame_count += 1
        current_time = time.time()
        elapsed = current_time - last_frame_time
        if elapsed > 0:
            current_fps = 1.0 / elapsed
        last_frame_time = current_time

        # Total processing time
        processing_time = (time.time() - frame_start) * 1000

        # Update shared metadata (thread-safe)
        with metadata_lock:
            latest_metadata['face_count'] = len(faces)
            latest_metadata['faces'] = [{'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
                                        for x, y, w, h in faces]
            latest_metadata['fps'] = round(current_fps, 1)
            latest_metadata['frame_number'] = frame_count
            latest_metadata['processing_time_ms'] = round(processing_time, 1)
            latest_metadata['detection_time_ms'] = round(detection_time, 1)

        # Encode frame as JPEG
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 80]
        ret, buffer = cv2.imencode('.jpg', frame, encode_param)

        if not ret:
            print("Failed to encode frame")
            continue

        frame_bytes = buffer.tobytes()

        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app.route('/')
def index():
    """Main camera viewer interface (iframe content)"""
    return render_template('index.html')


@app.route('/node')
def node_demo():
    """Example of how Node would embed the camera viewer"""
    return render_template('node.html')


@app.route('/video')
def video():
    """MJPEG video stream endpoint"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')


@socketio.on('connect')
def handle_connect():
    """Handle client connection"""
    print(f"Client connected: {datetime.now().isoformat()}")
    emit('status', {
        'connected': True,
        'detection_enabled': detection_enabled,
        'camera_resolution': f"{FRAME_WIDTH}x{FRAME_HEIGHT}",
        'target_fps': TARGET_FPS
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    print(f"Client disconnected: {datetime.now().isoformat()}")


@socketio.on('toggle_detection')
def handle_toggle_detection(data):
    """Toggle face detection on/off"""
    global detection_enabled
    detection_enabled = data.get('enabled', True)
    print(f"Detection {'enabled' if detection_enabled else 'disabled'}")
    emit('status', {'detection_enabled': detection_enabled})


@socketio.on('set_sensitivity')
def handle_set_sensitivity(data):
    """Adjust detection sensitivity (placeholder for future)"""
    threshold = data.get('threshold', 0.5)
    print(f"Sensitivity set to: {threshold}")
    emit('status', {'sensitivity': threshold, 'message': 'Sensitivity adjustment not yet implemented'})


@socketio.on('capture_snapshot')
def handle_capture_snapshot():
    """Capture and save current frame (placeholder for future)"""
    print("Snapshot requested")
    emit('status', {'message': 'Snapshot capture not yet implemented'})


@socketio.on('reset_calibration')
def handle_reset_calibration():
    """Reset calibration (placeholder for future)"""
    print("Calibration reset requested")
    emit('status', {'message': 'Calibration reset not yet implemented'})


if __name__ == '__main__':
    try:
        # Initialize camera and face detector
        camera = init_camera()
        face_cascade = init_face_detector()

        # Start metadata emitter thread
        emitter_thread = threading.Thread(target=metadata_emitter, daemon=True)
        emitter_thread.start()
        print("Metadata emitter thread started")

        print("\n" + "="*60)
        print("Camera Processing Demo Starting")
        print("="*60)
        print(f"Camera: /dev/video{CAMERA_DEVICE}")
        print(f"Resolution: {FRAME_WIDTH}x{FRAME_HEIGHT}")
        print(f"Target FPS: {TARGET_FPS}")
        print(f"Server: http://0.0.0.0:5500")
        print(f"Main viewer: http://0.0.0.0:5500/")
        print(f"Node demo: http://0.0.0.0:5500/node")
        print("="*60 + "\n")

        # Run Flask-SocketIO server
        socketio.run(app, host='0.0.0.0', port=5500, debug=False, allow_unsafe_werkzeug=True)

    except Exception as e:
        print(f"Error starting application: {e}")
        raise
    finally:
        if camera is not None:
            camera.release()
            print("Camera released")
