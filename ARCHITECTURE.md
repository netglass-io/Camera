# Camera Processing Demo - Architecture Document

## Project Overview

**Purpose**: Standalone camera processing demonstration for robotics team integration with Noblelift Fleet Management System.

**Goal**: Provide a working example of real-time camera feed processing with bidirectional communication between browser and processing backend, suitable for future integration into the Node driver interface.

**Use Case**: Process webcam feed for computer vision tasks (face detection demo, future pallet rack alignment) and display results to driver with overlay graphics and metadata.

## Design Constraints

### IP Separation
- This demo is intentionally **separate from the main Node codebase** to maintain IP boundaries
- Robotics team receives this standalone example without access to fleet management code
- Integration pattern documented but implementation remains in Node team's control

### Hardware Target
- **Primary deployment**: Jetson AGX Orin (agx1.simula.io)
- **Camera**: USB webcam at `/dev/video0`
- **GPU acceleration**: NVIDIA CUDA available for future optimization
- **Display**: Embedded in browser interface (2160x1440 on agx1)

### Latency Requirements
- Target: <100ms end-to-end (camera → processing → display)
- Critical for real-time driver guidance (pallet rack alignment)
- Optimized for local processing, minimal network overhead

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Jetson AGX Orin Device                  │
│                                                             │
│  ┌──────────┐      ┌─────────────────────┐                │
│  │ USB      │      │  Docker Container   │                │
│  │ Webcam   │──────│  (Port 5500)        │                │
│  │/dev/video│      │                     │                │
│  └──────────┘      │  ┌───────────────┐  │                │
│                    │  │ Python App    │  │                │
│                    │  │ - OpenCV      │  │                │
│                    │  │ - Face Detect │  │                │
│                    │  │ - Flask       │  │                │
│                    │  │ - SocketIO    │  │                │
│                    │  └───────┬───────┘  │                │
│                    │          │          │                │
│                    │  ┌───────┴───────┐  │                │
│                    │  │   HTTP Server │  │                │
│                    │  │   /video MJPEG│  │                │
│                    │  │   /socket.io  │  │                │
│                    │  │   /static/*   │  │                │
│                    │  └───────┬───────┘  │                │
│                    └──────────┼──────────┘                │
│                               │                            │
└───────────────────────────────┼────────────────────────────┘
                                │
                                ├─── HTTP  ──→  Video Stream (MJPEG)
                                ├─── WS    ──→  Metadata (JSON)
                                └─── WS    ←──  Driver Commands
                                │
                    ┌───────────▼────────────┐
                    │   Browser Client       │
                    │                        │
                    │  Video Feed            │
                    │  + Canvas Overlay      │
                    │  + Metadata Display    │
                    │  + Control Buttons     │
                    └────────────────────────┘
```

## Technology Stack

### Backend Processing (Python)
**Choice**: Python 3.11 with OpenCV
- **Rationale**:
  - Robotics team has ROS experience (typically Python/C++)
  - OpenCV is industry standard for computer vision
  - Abundant face detection examples available
  - Rapid prototyping for demo
  - Easy migration path to C++ if latency becomes critical

**Key Libraries**:
- `opencv-python`: Camera capture and face detection (Haar cascades)
- `Flask`: HTTP server for web interface
- `Flask-SocketIO`: WebSocket bidirectional communication
- `eventlet`: Async I/O for concurrent video streaming and WebSocket handling

### Video Streaming
**Choice**: MJPEG over HTTP
- **Rationale**:
  - Simplest implementation (<50 lines of code)
  - Low latency (~30-50ms)
  - No complex WebRTC signaling required for demo
  - Works in all browsers without additional libraries
  - Easy to add overlay graphics via HTML5 Canvas

**Alternative Considered**: WebRTC
- Pros: Lower latency, better quality
- Cons: Complex signaling, overkill for local LAN deployment
- Decision: MJPEG sufficient for demo, WebRTC available for future optimization

### Real-Time Communication
**Choice**: Flask-SocketIO (WebSocket-based)
- **Rationale**:
  - Similar pattern to SignalR used in Node/Hub
  - Bidirectional: Server pushes metadata, client sends commands
  - Event-based API familiar to robotics team
  - Easy to bridge to SignalR later for Node integration

**Communication Patterns**:
```python
# Server → Client (metadata push)
socketio.emit('camera_metadata', {
    'face_count': 2,
    'faces': [{'x': 100, 'y': 50, 'w': 80, 'h': 80}],
    'timestamp': time.time(),
    'fps': 30
})

# Client → Server (driver commands)
@socketio.on('start_alignment')
def handle_alignment():
    # Trigger pallet rack detection mode
    pass

@socketio.on('confirm_target')
def handle_confirm(data):
    # Lock onto target coordinates
    pass
```

### Frontend (HTML/JavaScript)
**Choice**: Vanilla JavaScript with SocketIO client
- **Rationale**:
  - Minimal dependencies
  - Clear example for robotics team
  - Easy to integrate into any framework later (Blazor, React, etc.)

**Key Components**:
- MJPEG `<img>` element for video stream
- HTML5 Canvas for overlay graphics (bounding boxes, alignment guides)
- SocketIO client for metadata and control
- Bootstrap 5 for basic styling (matches Node UI)

## Data Flow Architecture

### Video Stream Flow
```
Webcam → OpenCV VideoCapture → Frame Buffer
           ↓
    Face Detection (Haar Cascade)
           ↓
    Draw Bounding Boxes on Frame
           ↓
    JPEG Encode (quality=80, optimize for speed)
           ↓
    HTTP Response (multipart/x-mixed-replace)
           ↓
    Browser <img> Element
```

**Frame Rate**: Target 30 FPS, adjustable based on processing load

### Metadata Flow
```
Face Detection Results
    ↓
JSON Serialization
    ↓
SocketIO Emit ('camera_metadata')
    ↓
JavaScript Event Handler
    ↓
Update DOM (face count, coordinates)
    ↓
Optional: Update Canvas Overlay
```

**Update Rate**: Real-time on every processed frame (30 Hz)

### Command Flow
```
Driver Interaction (Button Click)
    ↓
JavaScript Event → SocketIO Emit ('command')
    ↓
Python Event Handler
    ↓
State Change in Processing Logic
    ↓
Acknowledgment via SocketIO
    ↓
UI Feedback
```

## Container Architecture

### Dockerfile Strategy
```dockerfile
FROM python:3.11-slim

# Install OpenCV dependencies (lightweight)
RUN apt-get update && apt-get install -y \
    libopencv-dev \
    python3-opencv \
    && rm -rf /var/lib/apt/lists/*

# Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY . /app
WORKDIR /app

EXPOSE 5500

CMD ["python", "app.py"]
```

### Docker Compose Configuration
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
      - /dev/video0:/dev/video0  # USB webcam access
    environment:
      - CAMERA_DEVICE=/dev/video0
      - FLASK_ENV=production
      - TARGET_FPS=30
    volumes:
      - ./logs:/app/logs  # Optional: Log persistence
```

**Key Configuration**:
- Port 5500 chosen to avoid conflicts with Node (5233), CanBridge (5000), CogNode (5001)
- Device passthrough for webcam access
- Environment variables for configuration without code changes
- Restart policy for production deployment

## Face Detection Implementation

### Haar Cascade Choice
**Model**: `haarcascade_frontalface_default.xml` (OpenCV built-in)
- **Rationale**:
  - Lightweight, fast inference (~10ms per frame)
  - No GPU required (CPU sufficient)
  - Good accuracy for frontal faces
  - Perfect for demo purposes

**Alternative for Production**:
- YOLO, SSD, or RetinaFace for better accuracy
- TensorRT optimization on Jetson for <5ms inference
- Future enhancement, not needed for demo

### Processing Pipeline
```python
def process_frame(frame):
    # Convert to grayscale (faster detection)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    # Draw bounding boxes
    for (x, y, w, h) in faces:
        cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)

    # Prepare metadata
    metadata = {
        'face_count': len(faces),
        'faces': [{'x': x, 'y': y, 'w': w, 'h': h} for x, y, w, h in faces],
        'timestamp': time.time()
    }

    return frame, metadata
```

## Future Integration with Node

### Integration Pattern 1: Iframe Embedding
**Node embeds camera demo as iframe**:
```razor
<!-- Node/Components/Pages/CameraView.razor -->
<iframe src="http://localhost:5500"
        width="100%"
        height="600px"
        style="border: none;">
</iframe>
```

**Pros**: Zero code changes to Camera demo
**Cons**: Limited cross-frame communication, separate authentication

### Integration Pattern 2: SignalR Bridge
**Camera service adds SignalR client to talk to Node**:
```python
# Camera app connects to Node as SignalR client
from signalrcore.hub_connection_builder import HubConnectionBuilder

node_connection = HubConnectionBuilder() \
    .with_url("http://localhost:5233/camerahub") \
    .build()

# Forward metadata to Node
node_connection.send("CameraMetadata", metadata)
```

**Pros**: Tight integration, Node controls routing to Hub
**Cons**: Camera demo now depends on Node architecture

### Integration Pattern 3: Node as Proxy
**Node proxies SocketIO <-> SignalR**:
```csharp
// Node/Services/CameraProxyService.cs
// Connect to Camera SocketIO
// Translate to SignalR for Hub/Browser consumption
```

**Pros**: Clean separation, Node controls data flow
**Cons**: Additional latency (~10-20ms), more complex Node code

**Recommendation**: Start with Pattern 1 (iframe) for demo, migrate to Pattern 3 for production.

## Driver Input Commands

### Command Types for Demo
```javascript
// Start/Stop processing
socket.emit('toggle_detection', {enabled: true});

// Change detection sensitivity
socket.emit('set_sensitivity', {threshold: 0.7});

// Capture snapshot
socket.emit('capture_snapshot');

// Reset/calibrate
socket.emit('reset_calibration');
```

### Future Pallet Rack Commands
```javascript
// Enable alignment mode
socket.emit('start_alignment', {mode: 'pallet_rack'});

// Confirm target selection
socket.emit('confirm_target', {target_id: 3});

// Request height adjustment
socket.emit('adjust_height', {target_height_mm: 1500});

// Cancel operation
socket.emit('cancel_alignment');
```

## CAN Bus Integration (Future)

### Architecture for Fork Control
```
Camera Container → SocketIO → Node → SignalR → CanBridge → CAN Bus → Curtis Controller
                                                                            ↓
                                                                       Fork Motors
```

**Data Flow Example**:
1. Camera detects pallet rack, calculates target height: 1500mm
2. Camera sends `adjust_height` command to Node (via SocketIO or SignalR)
3. Node validates command, sends to CanBridge
4. CanBridge translates to CAN message (Curtis protocol)
5. Curtis controller actuates hydraulic lift
6. Position feedback returns via CAN → CanBridge → Node → Camera
7. Camera adjusts guidance overlay based on actual fork position

**Safety Considerations**:
- All CAN commands must be validated by Node (driver authentication, safety checks)
- Camera service NEVER writes directly to CAN bus
- Emergency stop must override camera guidance
- Driver must confirm automated movements

## Performance Optimization

### Latency Budget
```
Camera capture:           16ms  (60 FPS)
Face detection:           10ms  (Haar cascade)
JPEG encoding:             5ms
Network transmission:     10ms  (local LAN)
Browser rendering:        16ms  (60 FPS)
─────────────────────────────
Total latency:            57ms  ✅ Target: <100ms
```

### Optimization Strategies
1. **Frame skipping**: Process every Nth frame if CPU overloaded
2. **Resolution reduction**: 640x480 sufficient for face detection
3. **GPU acceleration**: Use CUDA for future CNN-based detection
4. **Multi-threading**: Separate threads for capture, processing, streaming
5. **Adaptive quality**: Reduce JPEG quality under high load

### Monitoring Metrics
```python
# Expose metrics via SocketIO
socketio.emit('performance_metrics', {
    'fps': current_fps,
    'processing_time_ms': processing_time,
    'dropped_frames': dropped_frame_count,
    'cpu_usage': cpu_percent,
    'memory_mb': memory_usage
})
```

## Security Considerations

### Demo Security (Minimal)
- No authentication required (local development)
- Assumes trusted network (Jetson device only)
- CORS disabled for ease of integration

### Production Security (Future)
- **Authentication**: Token-based or certificate-based (match Node auth)
- **HTTPS/WSS**: Encrypted transport for video and commands
- **CORS**: Whitelist Node UI origin only
- **Rate limiting**: Prevent command flooding
- **Input validation**: Sanitize all driver commands

## Development Workflow

### Local Development (No Hardware)
```bash
# Use laptop webcam for development
python app.py

# Or mock camera with video file
python app.py --input test_video.mp4
```

### Deployment on Jetson
```bash
# Clone repo
git clone <repo-url> /home/nodemin/camera-demo
cd /home/nodemin/camera-demo

# Build and run
docker compose up -d

# View logs
docker compose logs -f

# Access UI
# http://agx1.simula.io:5500
```

### Testing Checklist
- [ ] Camera device detected (`/dev/video0`)
- [ ] Video stream displays in browser
- [ ] Face detection bounding boxes appear
- [ ] Metadata updates in real-time (face count)
- [ ] Control buttons trigger server responses
- [ ] Latency <100ms (use browser DevTools Network tab)
- [ ] Runs reliably for >1 hour without crashes

## Project Structure

```
Camera/
├── ARCHITECTURE.md          # This file
├── README.md                # Quick start guide
├── Dockerfile               # Container build
├── docker-compose.yml       # Deployment config
├── requirements.txt         # Python dependencies
├── app.py                   # Main Flask application
├── static/
│   ├── index.html          # Web viewer UI
│   ├── js/
│   │   └── viewer.js       # SocketIO client logic
│   └── css/
│       └── style.css       # Basic styling
├── models/
│   └── haarcascade_frontalface_default.xml  # Face detection model
├── tests/
│   ├── test_app.py         # Unit tests
│   └── test_video.mp4      # Mock input for testing
└── docs/
    └── INTEGRATION.md      # Node integration guide
```

## Success Criteria

### Demo Completion
- [x] Architecture documented
- [ ] Working face detection with live webcam
- [ ] Video stream viewable in browser
- [ ] Bidirectional SocketIO communication
- [ ] Overlay graphics (bounding boxes)
- [ ] Metadata display (face count)
- [ ] Control buttons (start/stop, sensitivity)
- [ ] Deployed on agx1 successfully
- [ ] Docker containerized
- [ ] Documentation for robotics team

### Robotics Team Handoff
- [ ] GitHub repo created (private)
- [ ] README with setup instructions
- [ ] Architecture document (this file)
- [ ] Integration guide for Node connection
- [ ] Example commands documented
- [ ] Performance metrics visible
- [ ] Code comments explaining key concepts

## Next Steps

### Phase 1: Core Demo (Immediate)
1. Implement `app.py` with Flask + OpenCV + SocketIO
2. Create `static/index.html` viewer with video and overlay
3. Add face detection with bounding boxes
4. Test on agx1 with USB webcam
5. Push to GitHub

### Phase 2: Enhancement (This Week)
1. Add control buttons (start/stop, sensitivity adjustment)
2. Implement performance metrics display
3. Add snapshot capture feature
4. Create integration guide for Node
5. Docker optimization (smaller image, faster build)

### Phase 3: Production Readiness (Next Sprint)
1. Replace face detection with pallet rack detection (robotics team task)
2. Add Node integration (iframe or SignalR bridge)
3. Implement authentication/authorization
4. Add CAN command pathway via Node
5. Safety validation layer
6. Load testing and optimization

## Questions for Robotics Team

Document these in README or initial meeting:

1. **Preferred language**: Python OK, or prefer C++ for performance?
2. **Existing models**: Do you have pre-trained pallet rack detection models?
3. **Input format**: Raw frames sufficient, or need specific preprocessing?
4. **Output format**: Bounding boxes + confidence scores sufficient?
5. **Control interface**: What driver inputs do you need (buttons, sliders, etc.)?
6. **Integration timeline**: When do you need Node integration complete?
7. **ROS dependency**: Do you need ROS bridge for existing tools?

## Technical Decisions Log

### Decision 1: Python vs C++
**Choice**: Python for demo
**Rationale**: Faster development, ROS experience, sufficient performance
**Review**: Re-evaluate if latency >100ms in practice

### Decision 2: MJPEG vs WebRTC
**Choice**: MJPEG
**Rationale**: Simplicity, low latency on local LAN
**Review**: Consider WebRTC if remote access needed

### Decision 3: SocketIO vs SignalR
**Choice**: SocketIO for demo
**Rationale**: Python ecosystem, simpler for robotics team
**Note**: SignalR bridge added during Node integration phase

### Decision 4: Haar Cascade vs CNN
**Choice**: Haar Cascade for demo
**Rationale**: Fast, no GPU required, sufficient for demo
**Note**: Robotics team will replace with their own models

### Decision 5: Standalone vs Integrated
**Choice**: Standalone container
**Rationale**: IP separation, cleaner demo, easier handoff
**Future**: Integrate via iframe or SignalR bridge

---

**Document Version**: 1.0
**Last Updated**: 2025-10-20
**Author**: James Laing + Claude
**Status**: Architecture Complete - Ready for Implementation
