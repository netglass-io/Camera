# Claude Session Handoff - Camera Demo Implementation

## Session Context

**Date**: 2025-10-20
**Current Location**: Local dev machine (`/home/jameslaing/Code/NobleOne/Camera`)
**Next Location**: AGX1 Jetson device (`agx1.simula.io`)
**Repository**: https://github.com/netglass-io/Camera (Public, MIT License)

## What Was Accomplished

### Repository Setup ✅
1. Created GitHub repository `netglass-io/Camera`
2. Made repository public with MIT license
3. Created comprehensive documentation:
   - `ARCHITECTURE.md` - Complete technical design (19.6 KB)
   - `README.md` - Quick start and team guidance
   - `NEXT_SESSION.md` - Implementation roadmap
   - `CLAUDE-HANDOFF.md` - This file
   - `LICENSE` - MIT License
   - `.gitignore` - Python/Docker development

### Key Decisions Made
1. **Public repository** - For easy distribution, can make private if team prefers
2. **MIT License** - Permissive, allows team full flexibility
3. **Python + OpenCV + Flask-SocketIO** - Suggested stack (team can change)
4. **MJPEG streaming** - Suggested approach (team can change)
5. **Port 5500** - Avoids conflicts with Node (5233), CanBridge (5000), CogNode (5001)
6. **Standalone container** - Maintains IP separation from Node codebase
7. **Face detection** - Placeholder for team's pallet rack detection

### Important Context for Robotics Team
- Demo is **NOT yet functional** - only documentation exists
- All architecture decisions are **flexible and open for debate**
- Team can use this repo as primary workspace OR just as reference
- Only requirement: display processed camera video in web browser for Node integration
- Repository can be made private at team's request

## Current State

### Files in Repository
```
Camera/
├── ARCHITECTURE.md          # Complete technical design
├── README.md                # Quick start + team guidance
├── NEXT_SESSION.md          # Implementation roadmap
├── CLAUDE-HANDOFF.md        # This handoff document
├── LICENSE                  # MIT License
└── .gitignore              # Python/Docker gitignore

NOT YET CREATED:
├── requirements.txt         # Python dependencies
├── app.py                   # Flask server + OpenCV
├── Dockerfile              # Container build
├── docker-compose.yml      # Deployment config
├── static/
│   ├── index.html          # Web viewer
│   ├── js/viewer.js        # SocketIO client
│   └── css/style.css       # Styling
└── models/                 # Face detection models
```

### Git Status
- Branch: `main`
- Total commits: 6
- Last commit: `bfaf217` - "Add note about repository visibility flexibility"
- Clean working directory (all changes committed and pushed)

## Next Session: Implementation on AGX1

### Session Goal
Create working demo with:
- USB webcam video streaming
- Face detection with bounding boxes
- Browser-based viewer
- Bidirectional SocketIO communication
- Docker containerized deployment

### Prerequisites on AGX1

#### 1. Hardware
- USB webcam connected at `/dev/video0`
- Verify with: `ls -la /dev/video*`
- User `nodemin` in `video` group for camera access

#### 2. Repository Clone
```bash
ssh nodemin@agx1.simula.io
cd /home/nodemin
mkdir -p Code/NobleOne
cd Code/NobleOne
git clone https://github.com/netglass-io/Camera.git
cd Camera
```

#### 3. Development Tools
- Docker and Docker Compose (already installed)
- Python 3.11 (for local testing before containerization)
- Text editor (vim, nano, or VS Code remote)

### Implementation Order

#### Phase 1: Core Application (30-45 min)
1. **requirements.txt**
   ```
   Flask==3.0.0
   Flask-SocketIO==5.3.5
   opencv-python==4.8.1.78
   eventlet==0.33.3
   python-socketio==5.10.0
   ```

2. **app.py** - Flask server with:
   - Camera initialization (`cv2.VideoCapture(0)`)
   - Face detection (Haar cascade)
   - MJPEG stream generator (`/video` endpoint)
   - SocketIO server for metadata
   - Command handlers (toggle detection, sensitivity)
   - Main page route (`/`)

3. **static/index.html** - Web viewer with:
   - Video stream display (`<img src="/video">`)
   - Metadata display (face count, FPS)
   - Control buttons (start/stop, sensitivity)
   - SocketIO client connection
   - Bootstrap 5 for styling

4. **static/js/viewer.js** - SocketIO client:
   - Connect to server
   - Listen for `camera_metadata` events
   - Listen for `performance_metrics` events
   - Send commands (toggle, sensitivity, etc.)
   - Update DOM with metadata

5. **static/css/style.css** - Basic styling:
   - Full-width video display
   - Metadata overlay or sidebar
   - Button styling matching Node UI

#### Phase 2: Local Testing (15 min)
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test in browser
# http://agx1.simula.io:5500

# Verify:
# - Video stream displays
# - Face detection boxes appear
# - Metadata updates (face count)
# - Commands work (start/stop)
```

#### Phase 3: Docker Deployment (30 min)
1. **Dockerfile**
   ```dockerfile
   FROM python:3.11-slim

   # OpenCV dependencies
   RUN apt-get update && apt-get install -y \
       libopencv-dev \
       python3-opencv \
       && rm -rf /var/lib/apt/lists/*

   WORKDIR /app
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   COPY . .

   EXPOSE 5500
   CMD ["python", "app.py"]
   ```

2. **docker-compose.yml**
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

3. **Build and test**
   ```bash
   docker compose build
   docker compose up -d
   docker compose logs -f

   # Test at http://agx1.simula.io:5500
   ```

#### Phase 4: Documentation & Git (15 min)
1. Update README.md status section (mark as functional)
2. Add any AGX1-specific notes to NEXT_SESSION.md
3. Document any issues encountered
4. Commit and push:
   ```bash
   git add .
   git commit -m "Implement working camera demo with face detection"
   git push origin main
   ```

### Implementation Skeleton

#### app.py Structure
```python
from flask import Flask, Response, render_template
from flask_socketio import SocketIO, emit
import cv2
import time
import threading
from datetime import datetime

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global state
camera = None
face_cascade = None
detection_enabled = True
current_fps = 0
last_frame_time = time.time()

def init_camera():
    """Initialize USB webcam"""
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    return cap

def detect_faces(frame):
    """Detect faces in frame using Haar cascade"""
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )
    return faces

def generate_frames():
    """Generate MJPEG stream with face detection"""
    global current_fps, last_frame_time

    while True:
        success, frame = camera.read()
        if not success:
            break

        start_time = time.time()

        # Face detection
        faces = []
        if detection_enabled:
            faces = detect_faces(frame)

            # Draw bounding boxes
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

        # Calculate FPS
        current_fps = 1.0 / (time.time() - last_frame_time)
        last_frame_time = time.time()

        # Emit metadata via SocketIO
        processing_time = (time.time() - start_time) * 1000
        socketio.emit('camera_metadata', {
            'face_count': len(faces),
            'faces': [{'x': int(x), 'y': int(y), 'w': int(w), 'h': int(h)}
                      for x, y, w, h in faces],
            'fps': round(current_fps, 1),
            'timestamp': datetime.now().isoformat()
        })

        socketio.emit('performance_metrics', {
            'processing_time_ms': round(processing_time, 1),
            'fps': round(current_fps, 1)
        })

        # Encode frame as JPEG
        ret, buffer = cv2.imencode('.jpg', frame,
                                   [cv2.IMWRITE_JPEG_QUALITY, 80])
        frame_bytes = buffer.tobytes()

        # Yield frame in multipart format
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/')
def index():
    """Serve main page"""
    return render_template('index.html')

@app.route('/video')
def video():
    """Video stream endpoint"""
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@socketio.on('connect')
def handle_connect():
    """Client connected"""
    print('Client connected')
    emit('status', {'connected': True, 'detection_enabled': detection_enabled})

@socketio.on('disconnect')
def handle_disconnect():
    """Client disconnected"""
    print('Client disconnected')

@socketio.on('toggle_detection')
def handle_toggle(data):
    """Toggle face detection on/off"""
    global detection_enabled
    detection_enabled = data.get('enabled', True)
    emit('status', {'detection_enabled': detection_enabled})

@socketio.on('set_sensitivity')
def handle_sensitivity(data):
    """Adjust detection sensitivity (placeholder)"""
    threshold = data.get('threshold', 0.5)
    emit('status', {'sensitivity': threshold})

if __name__ == '__main__':
    # Initialize camera and face detector
    camera = init_camera()
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    print('Starting camera demo on port 5500...')
    socketio.run(app, host='0.0.0.0', port=5500, debug=False)
```

#### static/index.html Structure
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Camera Demo - Face Detection</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="/static/css/style.css">
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-9">
                <h2>Camera Feed</h2>
                <img id="video-stream" src="/video" class="img-fluid">
            </div>
            <div class="col-md-3">
                <h3>Metadata</h3>
                <div class="card">
                    <div class="card-body">
                        <p>Faces Detected: <strong id="face-count">0</strong></p>
                        <p>FPS: <strong id="fps">0</strong></p>
                        <p>Latency: <strong id="latency">0</strong> ms</p>
                    </div>
                </div>

                <h3 class="mt-4">Controls</h3>
                <div class="card">
                    <div class="card-body">
                        <div class="form-check form-switch mb-3">
                            <input class="form-check-input" type="checkbox"
                                   id="toggle-detection" checked
                                   onchange="toggleDetection()">
                            <label class="form-check-label" for="toggle-detection">
                                Enable Detection
                            </label>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script src="/static/js/viewer.js"></script>
</body>
</html>
```

#### static/js/viewer.js Structure
```javascript
const socket = io();

socket.on('connect', () => {
    console.log('Connected to camera service');
});

socket.on('disconnect', () => {
    console.log('Disconnected from camera service');
});

socket.on('camera_metadata', (data) => {
    document.getElementById('face-count').textContent = data.face_count;
    document.getElementById('fps').textContent = data.fps;
});

socket.on('performance_metrics', (data) => {
    document.getElementById('latency').textContent =
        data.processing_time_ms.toFixed(1);
});

socket.on('status', (data) => {
    console.log('Status:', data);
});

function toggleDetection() {
    const enabled = document.getElementById('toggle-detection').checked;
    socket.emit('toggle_detection', {enabled: enabled});
}
```

### Testing Checklist

After implementation, verify:
- [ ] Camera device accessible at `/dev/video0`
- [ ] Python dependencies installed without errors
- [ ] Local test: `python app.py` runs without errors
- [ ] Video stream displays at http://agx1.simula.io:5500
- [ ] Face detection boxes appear when standing in front of camera
- [ ] Metadata updates in real-time (face count, FPS)
- [ ] Toggle detection button works
- [ ] Docker build succeeds
- [ ] Docker container runs and restarts
- [ ] Container logs show no errors
- [ ] Performance: Latency <100ms, FPS >20
- [ ] Runs stable for >5 minutes without crashes

### Success Criteria

Session complete when:
1. ✅ Working demo accessible at http://agx1.simula.io:5500
2. ✅ Live video stream from USB webcam
3. ✅ Face detection with bounding boxes
4. ✅ Real-time metadata display
5. ✅ Bidirectional commands working
6. ✅ Docker containerized
7. ✅ Code committed and pushed to GitHub
8. ✅ Performance targets met (<100ms latency, >20 FPS)

### Known Issues / Considerations

1. **Camera permissions**: May need to add `nodemin` to `video` group
2. **OpenCV dependencies**: Docker image may need additional system libraries
3. **Port conflicts**: Ensure 5500 not already in use on AGX1
4. **Face cascade model**: Using OpenCV's built-in model (no download needed)
5. **Performance**: May need to reduce resolution if FPS drops below target

### Integration with Node (Future)

Once demo is working and robotics team validates approach:
1. Node can embed via iframe: `<iframe src="http://localhost:5500">`
2. Or create SignalR bridge for tighter integration
3. Camera service can add Node authentication
4. Add CAN command pathway for fork control via Node

### Robotics Team Handoff

After demo is working:
1. Share GitHub repository URL (already public)
2. Schedule demo call to show working face detection
3. Walk through architecture decisions
4. Gather their requirements for pallet rack detection
5. Discuss integration timeline with Node
6. Create GitHub Issues for their questions/changes

## Environment Information

### AGX1 Device
- **Hostname**: agx1.simula.io (or agx1.local)
- **SSH**: `ssh nodemin@agx1.simula.io`
- **Password**: Welcome7
- **Display**: 2160x1440 (2K display)
- **Docker**: Installed and configured
- **User**: nodemin (should be in docker and video groups)

### Port Allocations
- **5000**: CanBridge DataService
- **5001**: CogNode (AI service)
- **5233**: Node driver interface
- **5500**: Camera demo (this project)

### Related Projects
- **Node**: `/home/nodemin/Code/NobleOne/Node` (driver interface)
- **CanBridge**: Separate repo (CAN data service)
- **Hub**: Separate repo (cloud fleet management)

## Questions to Ask During Implementation

If you encounter decisions during implementation:
1. **Python version conflicts?** - Use Python 3.11 if available, 3.9+ acceptable
2. **OpenCV installation issues?** - Try `opencv-python-headless` instead
3. **Camera not detected?** - Check `/dev/video*` and permissions
4. **Port conflict?** - Can change to 5501 or other free port
5. **Performance issues?** - Reduce resolution, lower FPS target, skip frames

## Git Workflow Reminder

**Branch Policy**: Feature branches for all work
```bash
# Create feature branch
git checkout -b feature/camera-demo-implementation

# Make changes and commit
git add .
git commit -m "Implement camera demo with face detection"

# Push feature branch
git push origin feature/camera-demo-implementation

# Create PR via gh CLI or GitHub web
gh pr create --title "Implement camera demo" --body "Working face detection demo"

# After merge, cleanup
git checkout main
git pull origin main
git branch -d feature/camera-demo-implementation
```

**Note**: For this demo repo, direct commits to main are acceptable since it's example code. But if robotics team adopts as primary repo, use feature branch workflow.

## Final Notes

- This is a **reference implementation** - team can change anything
- Focus on **working demo first**, optimization later
- **Document issues** encountered for team's benefit
- **Take screenshots** of working demo for documentation
- **Measure performance** (latency, FPS) to validate targets

---

**Estimated Time**: 2-3 hours for complete implementation
**Priority**: Medium (robotics team needs reference soon)
**Status**: Ready to begin implementation on AGX1
**Contact**: james@netglass.io for questions
