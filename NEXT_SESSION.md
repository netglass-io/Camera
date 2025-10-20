# Next Session: AGX1 Implementation

## Session Goal
Implement working camera demo with face detection on agx1 Jetson device.

## Prerequisites Completed ✅
1. ✅ GitHub repository created: https://github.com/netglass-io/Camera
2. ✅ Repository is public with MIT license
3. ✅ Architecture documented in ARCHITECTURE.md
4. ✅ Quick start guide in README.md
5. ✅ Git initialized and pushed to GitHub

## On AGX1: Setup Steps

### 1. Clone Repository
```bash
ssh nodemin@agx1.simula.io
cd /home/nodemin/Code
mkdir -p NobleOne
cd NobleOne
git clone https://github.com/netglass-io/Camera.git
cd Camera
```

### 2. Verify Webcam
```bash
# Check camera device
ls -la /dev/video*

# Test camera (if v4l-utils installed)
v4l2-ctl --device=/dev/video0 --list-formats

# If needed, add user to video group
sudo usermod -aG video nodemin
# Then logout/login for group to take effect
```

## Implementation Checklist

### Phase 1: Core Files (Implement First)
- [ ] `requirements.txt` - Python dependencies
- [ ] `app.py` - Flask server with OpenCV face detection
- [ ] `static/index.html` - Web viewer interface
- [ ] `static/js/viewer.js` - SocketIO client logic
- [ ] `static/css/style.css` - Basic styling
- [ ] `models/haarcascade_frontalface_default.xml` - Face detection model

### Phase 2: Docker Deployment
- [ ] `Dockerfile` - Container build
- [ ] `docker-compose.yml` - Deployment config
- [ ] Test build: `docker compose build`
- [ ] Test run: `docker compose up`
- [ ] Verify at: http://agx1.simula.io:5500

### Phase 3: Testing & Documentation
- [ ] Test video stream displays
- [ ] Test face detection bounding boxes
- [ ] Test metadata updates (face count)
- [ ] Test bidirectional commands (start/stop)
- [ ] Measure latency (<100ms target)
- [ ] Document any issues in GitHub Issues
- [ ] Create INTEGRATION.md for Node connection guide

## Key Implementation Notes

### Flask App Structure (`app.py`)
```python
from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
import cv2
import time
import threading

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
camera = None
face_cascade = None
detection_enabled = True

def init_camera():
    """Initialize webcam"""
    cap = cv2.VideoCapture(0)  # /dev/video0
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    return cap

def generate_frames():
    """Generate MJPEG stream"""
    while True:
        # Capture frame
        # Detect faces
        # Draw bounding boxes
        # Emit metadata via SocketIO
        # Yield JPEG frame
        pass

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video')
def video():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('toggle_detection')
def handle_toggle(data):
    global detection_enabled
    detection_enabled = data['enabled']
    emit('status', {'detection_enabled': detection_enabled})

if __name__ == '__main__':
    camera = init_camera()
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )
    socketio.run(app, host='0.0.0.0', port=5500, debug=False)
```

### SocketIO Client (`static/js/viewer.js`)
```javascript
const socket = io();

socket.on('connect', () => {
    console.log('Connected to camera service');
});

socket.on('camera_metadata', (data) => {
    document.getElementById('face-count').textContent = data.face_count;
    document.getElementById('fps').textContent = data.fps.toFixed(1);
});

socket.on('performance_metrics', (data) => {
    document.getElementById('latency').textContent =
        data.processing_time_ms.toFixed(1) + ' ms';
});

function toggleDetection() {
    const enabled = document.getElementById('toggle-btn').checked;
    socket.emit('toggle_detection', {enabled: enabled});
}
```

### Docker Compose Config
```yaml
version: '3.8'
services:
  camera-demo:
    build: .
    container_name: camera-demo
    restart: unless-stopped
    ports:
      - "5500:5500"
    devices:
      - /dev/video0:/dev/video0
    environment:
      - CAMERA_DEVICE=/dev/video0
      - TARGET_FPS=30
      - FLASK_ENV=production
```

## Expected Outcomes

After this session:
1. ✅ Working demo accessible at http://agx1.simula.io:5500
2. ✅ Live video stream from USB webcam
3. ✅ Face detection with green bounding boxes
4. ✅ Real-time metadata (face count, FPS)
5. ✅ Bidirectional commands (start/stop detection)
6. ✅ Latency <100ms end-to-end
7. ✅ Docker containerized and deployable

## Handoff to Robotics Team

Once demo is working:
1. Share GitHub repository access
2. Schedule demo session (show face detection working)
3. Walk through ARCHITECTURE.md
4. Discuss their pallet rack detection requirements
5. Create GitHub Issues for their questions
6. Plan integration timeline with Node

## Questions to Ask Robotics Team

During handoff demo:
1. Is Python + OpenCV acceptable for your needs?
2. Do you have existing pallet rack detection models?
3. What metadata do you need from detection? (distance, pose, etc.)
4. What driver controls do you need? (start alignment, confirm target, etc.)
5. When do you need full Node integration?
6. Do you need ROS bridge for existing tools?

## Performance Targets

- **Latency**: <100ms (camera → display)
- **Frame Rate**: 30 FPS
- **CPU Usage**: <50% on Jetson AGX Orin
- **Memory**: <500MB
- **Stability**: Run for >1 hour without crashes

## Integration Plan (Future Session)

After robotics team validates demo:
1. Replace face detection with pallet rack detection
2. Add alignment overlay graphics
3. Implement Node iframe embedding or SignalR bridge
4. Add authentication via Node certificates
5. Create CAN command pathway for fork control
6. Add safety validation layer

---

**Ready to Start**: Pull this repo on agx1 and begin implementation!
**Estimated Time**: 2-3 hours for working demo
**Contact**: james@netglass.io
