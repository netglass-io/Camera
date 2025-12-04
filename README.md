# Camera Processing Demo

> Real-time camera processing with face detection, video streaming, and bidirectional browser communication for robotics integration.

## 🎯 See It In Action

**Want to see how this integrates with Node?**

Visit **[http://localhost:5501/node](http://localhost:5501/node)** after starting the container to see a live demonstration of how the Camera application appears embedded within the Node driver interface.

This demo page shows:
- The Camera app running in an iframe (just like in production Node)
- Node-style navigation sidebar
- Full-screen iframe layout matching the actual deployment

## ⚠️ Important Notes for Robotics Team

### Current Status
**✅ This demo is FULLY FUNCTIONAL and ready to use!**

- ✅ Real-time video streaming with face detection
- ✅ Bidirectional SocketIO communication
- ✅ Docker containerized with NVIDIA GPU runtime
- ✅ Web-based viewer with live metadata
- ✅ **Node integration demo at /node**
- ✅ Tested and verified on Jetson AGX Orin

**Note on GPU**: The container has NVIDIA GPU runtime configured correctly, but currently uses CPU-based face detection (Haar Cascade). This is intentional and provides good performance (~30 FPS). See `GPU-STATUS.md` for details on GPU configuration and how to add GPU-accelerated models.

### Repository Visibility
This repository is currently **public** for quick and easy distribution. If you prefer to work in a private repository, we can change the visibility at any time. Just let us know your preference.

### Purpose of This Repository
This repository provides an **example architecture** for displaying post-processed camera video streams in a web browser interface. The goal is to demonstrate one possible approach for:
- Streaming processed video to a web UI
- Sending metadata alongside video (detection results, coordinates, etc.)
- Receiving commands from the browser (start/stop, adjust settings, etc.)

### How to Use This Repository

You have complete flexibility in how to use this work:

1. **Use as your primary repo** - If this architecture is helpful, feel free to develop directly in this repository
2. **Use as reference only** - Take the concepts and implement your own solution differently
3. **Propose changes** - All architecture decisions (Python vs C++, MJPEG vs WebRTC, Flask vs other frameworks) are **open for discussion and change**

**The only requirement**: Provide a way to display post-processed camera feeds in a web browser that can eventually integrate with the Node driver interface.

### What's Open for Debate
- Programming language (Python, C++, Rust, etc.)
- Video streaming method (MJPEG, WebRTC, HLS, etc.)
- Communication protocol (SocketIO, SignalR, plain WebSockets, etc.)
- Detection algorithms (face detection is just a placeholder)
- Deployment approach (Docker, native binary, ROS nodes, etc.)
- Everything else!

### What Matters
- Displaying processed video in a browser
- Low latency for real-time driver guidance
- Ability to integrate with Node UI eventually (iframe, API, or other method)

---

## Quick Start

### Prerequisites
- Docker and Docker Compose installed
- USB webcam connected (will appear as `/dev/video0`)
- Target device: Jetson AGX Orin (or similar Linux system)

### Option 1: Use Pre-Built Container (Recommended)

The container is automatically built and published to GitHub Container Registry:

```bash
# Pull the latest image
docker pull ghcr.io/netglass-io/camera:latest

# Or use docker-compose with the pre-built image
# Edit docker-compose.yml to use:
#   image: ghcr.io/netglass-io/camera:latest
# instead of:
#   build: .

docker compose up -d
```

### Option 2: Build Locally

```bash
# Clone repository
git clone https://github.com/netglass-io/Camera.git
cd Camera

# Build and run
docker compose build
docker compose up -d

# View logs
docker compose logs -f

# Access web interface
# http://<device-ip>:5501 (Docker)
# http://<device-ip>:5500 (local Python)
```

### Stop Service

```bash
docker compose down
```

## What This Demo Will Provide (Once Implemented)

### Planned Features
- **Real-time video streaming** - MJPEG stream from USB webcam (or alternative method)
- **Face detection** - OpenCV Haar cascade with bounding boxes (placeholder for your detection algorithm)
- **Bidirectional communication** - WebSocket (SocketIO) for metadata and commands
- **Browser-based viewer** - HTML5 with canvas overlay
- **Performance metrics** - FPS, processing time, frame drops
- **Interactive controls** - Start/stop, sensitivity adjustment
- **Docker containerized** - Easy deployment and reproducibility

### Architecture

```
USB Webcam → Docker Container (Python/OpenCV) → Browser
                      ↓
             Port 5500: HTTP + WebSocket
                      ↓
         ┌────────────┴────────────┐
         │                         │
    Video Stream              Metadata/Commands
    (MJPEG /video)            (SocketIO /socket.io)
```

## Integration with Node UI

This demo is designed to integrate with the Noblelift Fleet Management Node driver interface.

### Integration Options

**Option 1: Iframe Embedding** (Simplest)
```html
<iframe src="http://localhost:5500" width="100%" height="600px"></iframe>
```

**Option 2: SignalR Bridge** (Production)
- Camera service adds SignalR client to communicate with Node
- Node routes camera data to Hub and driver interface
- See `docs/INTEGRATION.md` for implementation guide

**Option 3: Node as Proxy**
- Node proxies SocketIO ↔ SignalR translation
- Maintains clean separation between camera service and Node code

## Development

### Local Development (Without Jetson)

```bash
# Install Python dependencies
pip install -r requirements.txt

# Run with local webcam
python app.py

# Or use test video file
python app.py --input tests/test_video.mp4
```

Access at: http://localhost:5500

### Project Structure

```
Camera/
├── app.py                   # Main Flask application
├── Dockerfile              # Container build
├── docker-compose.yml      # Deployment config
├── requirements.txt        # Python dependencies
├── static/
│   ├── index.html         # Web viewer
│   ├── js/viewer.js       # SocketIO client
│   └── css/style.css      # Styling
├── models/
│   └── haarcascade_*.xml  # Face detection model
└── docs/
    ├── ARCHITECTURE.md    # Technical design document
    └── INTEGRATION.md     # Node integration guide
```

## Technology Stack

- **Backend**: Python 3.11 + Flask + Flask-SocketIO
- **Computer Vision**: OpenCV (opencv-python)
- **Video Streaming**: MJPEG over HTTP (low latency)
- **Real-time Communication**: WebSocket (SocketIO)
- **Frontend**: HTML5 + Canvas + Bootstrap 5
- **Container**: Docker with device passthrough

## Configuration

### Environment Variables

Set in `docker-compose.yml` or `.env` file:

```bash
CAMERA_DEVICE=/dev/video0    # Webcam device path
TARGET_FPS=30                # Target frame rate
FLASK_ENV=production         # Flask environment
DETECTION_SCALE=1.1          # Face detection sensitivity
MIN_NEIGHBORS=5              # Face detection quality
```

### Port Configuration

Default port: **5500**

To change, edit `docker-compose.yml`:
```yaml
ports:
  - "5501:5500"  # Host:Container
```

## SocketIO Events

### Server → Client (Metadata Push)

```javascript
socket.on('camera_metadata', (data) => {
    console.log('Faces detected:', data.face_count);
    console.log('Face coordinates:', data.faces);
    console.log('FPS:', data.fps);
});

socket.on('performance_metrics', (data) => {
    console.log('Processing time:', data.processing_time_ms);
    console.log('CPU usage:', data.cpu_usage);
});
```

### Client → Server (Commands)

```javascript
// Toggle detection on/off
socket.emit('toggle_detection', {enabled: true});

// Adjust sensitivity
socket.emit('set_sensitivity', {threshold: 0.7});

// Capture snapshot
socket.emit('capture_snapshot');

// Reset calibration
socket.emit('reset_calibration');
```

## Performance

### Target Metrics
- **Latency**: <100ms end-to-end
- **Frame Rate**: 30 FPS
- **CPU Usage**: <50% on Jetson AGX Orin
- **Memory**: <500MB

### Optimization Tips
1. Reduce camera resolution for faster processing
2. Adjust `TARGET_FPS` if CPU overloaded
3. Use GPU acceleration for CNN-based models (future)
4. Enable frame skipping under high load

## Extending for Pallet Rack Detection

This demo uses face detection as a placeholder. To adapt for pallet rack detection:

### Replace Detection Algorithm

```python
# In app.py, replace face detection with your model:

# Old:
faces = face_cascade.detectMultiScale(gray, ...)

# New:
racks = pallet_detector.detect(frame)
# Returns: [{'x', 'y', 'w', 'h', 'confidence', 'distance_mm'}]
```

### Add Custom Metadata

```python
metadata = {
    'rack_count': len(racks),
    'racks': racks,
    'alignment_status': 'aligned' if check_alignment(racks) else 'offset',
    'target_height_mm': calculate_target_height(racks),
    'recommended_action': 'lift' | 'lower' | 'forward' | 'backward'
}
```

### Update Overlay Graphics

```javascript
// In viewer.js, draw alignment guides instead of face boxes
function drawAlignmentGuide(rack) {
    // Draw crosshairs
    // Draw distance indicators
    // Draw recommended actions
}
```

## Troubleshooting

### Camera Not Detected

```bash
# Check if camera is connected
ls -la /dev/video*

# Test camera with v4l2
v4l2-ctl --device=/dev/video0 --list-formats

# If permission denied, add user to video group
sudo usermod -aG video nodemin
```

### Container Fails to Start

```bash
# Check logs
docker compose logs

# Common issues:
# - Camera device not passed through (check docker-compose.yml devices:)
# - Port 5500 already in use (change port mapping)
# - Missing dependencies (rebuild: docker compose build --no-cache)
```

### Low Frame Rate

```bash
# Reduce camera resolution in app.py:
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

# Or reduce target FPS:
TARGET_FPS=15
```

### High CPU Usage

```bash
# Enable frame skipping (process every Nth frame)
PROCESS_EVERY_N_FRAMES=2

# Or reduce detection frequency
DETECTION_INTERVAL_MS=100
```

## Testing

### Unit Tests

```bash
pytest tests/
```

### Manual Testing

1. **Video Stream**: Navigate to http://localhost:5500, verify video displays
2. **Face Detection**: Stand in front of camera, verify green bounding box
3. **Metadata**: Check face count updates in real-time
4. **Commands**: Click control buttons, verify server response
5. **Performance**: Check metrics display, ensure FPS >20
6. **Latency**: Wave hand in front of camera, measure delay (<100ms)

### Load Testing

```bash
# Run for extended period
docker compose up -d
# Monitor for 1+ hour, check for memory leaks or crashes
docker stats camera-demo
```

## Security Notes

### Demo Mode (Current)
- ⚠️ No authentication required
- ⚠️ Assumes trusted network
- ⚠️ HTTP only (no encryption)

### Production Recommendations
- [ ] Add token-based authentication
- [ ] Enable HTTPS/WSS
- [ ] Implement CORS whitelist
- [ ] Add rate limiting
- [ ] Validate all driver commands
- [ ] Audit camera access permissions

## Future Enhancements

### Planned Features
- [ ] Multiple camera support
- [ ] Recording and playback
- [ ] Snapshot gallery
- [ ] Historical analytics
- [ ] ML model hot-swapping
- [ ] GPU acceleration (CUDA)
- [ ] ROS bridge for existing tools

### Integration Roadmap
- [ ] SignalR bridge to Node
- [ ] Authentication via Node certificates
- [ ] CAN command pathway for fork control
- [ ] Safety validation layer
- [ ] Manager dashboard view

## Support

### Documentation
- **Architecture**: See `docs/ARCHITECTURE.md` for technical design
- **Integration**: See `docs/INTEGRATION.md` for Node connection guide
- **API Reference**: See inline code comments in `app.py`

### Questions for Robotics Team

Before starting development, please answer:

1. **Language preference**: Python OK, or prefer C++ for performance?
2. **Existing models**: Do you have pre-trained pallet rack detection models?
3. **Input requirements**: Raw frames sufficient, or need specific preprocessing?
4. **Output format**: What metadata do you need (bounding boxes, distance, pose)?
5. **Driver controls**: What inputs do you need from driver (start/stop, confirm target, etc.)?
6. **Integration timeline**: When do you need full Node integration?
7. **ROS dependency**: Do you need ROS bridge for existing tools?

Please document answers in GitHub Issues or initial planning meeting notes.

## License

MIT License - see [LICENSE](LICENSE) file for details.

This is an open-source demo/reference implementation. Feel free to use, modify, and distribute.

---

**Version**: 1.0.0
**Last Updated**: 2025-10-20
**Status**: Architecture Complete - Ready for Implementation
**Contact**: james@netglass.io
