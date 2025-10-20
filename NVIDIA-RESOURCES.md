# NVIDIA Jetson Camera Processing Resources

## Overview

This document lists official and community NVIDIA resources for building containerized camera processing applications on Jetson hardware with GPU acceleration.

---

## 🌟 Recommended: dusty-nv/jetson-inference

**Repository**: https://github.com/dusty-nv/jetson-inference

### Why This is Perfect for Our Use Case

1. ✅ **Complete Docker setup** - `docker/run.sh` handles everything
2. ✅ **Camera support built-in** - V4L2 USB cameras and MIPI CSI cameras
3. ✅ **Hardware acceleration** - TensorRT GPU optimization
4. ✅ **Well-documented tutorials** - "Hello AI World" guide
5. ✅ **Active maintenance** - Regular updates from NVIDIA engineer Dustin Franklin
6. ✅ **Python + C++ examples** - Easy to adapt

### Quick Start

```bash
# Clone repository
git clone --recursive --depth=1 https://github.com/dusty-nv/jetson-inference
cd jetson-inference

# Run Docker container (auto-pulls correct image for your JetPack version)
docker/run.sh

# Inside container, test camera
video-viewer /dev/video0        # For USB webcam
video-viewer csi://0            # For MIPI CSI camera
```

### What It Provides

- **Docker container** with all dependencies pre-installed
- **Camera utilities** (`video-viewer`, `video-capture`)
- **DNN vision primitives**:
  - `imageNet` - Image classification
  - `detectNet` - Object detection
  - `segNet` - Semantic segmentation
  - `poseNet` - Pose estimation
  - `actionNet` - Action recognition
- **Python bindings** for all functionality
- **Network streaming** (RTP, RTSP, WebRTC)

### Docker Hub

Pre-built images available at: https://hub.docker.com/r/dustynv/jetson-inference

### Documentation

- Main docs: https://github.com/dusty-nv/jetson-inference
- Docker guide: https://github.com/dusty-nv/jetson-inference/blob/master/docs/aux-docker.md
- Dockerfile: https://github.com/dusty-nv/jetson-inference/blob/master/Dockerfile

### Relevance to Our Demo

**Perfect for**:
- Understanding how to properly mount camera devices in Docker
- Hardware-accelerated video processing examples
- Streaming processed video over network
- Python API examples for camera capture and processing

**Can adapt for our use case**:
- Replace their DNN inference with our face/pallet detection
- Use their camera utilities as reference for webcam access
- Adapt their Docker setup for our Flask/SocketIO approach
- Learn their streaming setup for web browser delivery

---

## 🔧 Alternative: NVIDIA DeepStream SDK

**Repository**: https://github.com/NVIDIA-AI-IOT/deepstream_dockers
**Documentation**: https://docs.nvidia.com/metropolis/deepstream/dev-guide/text/DS_docker_containers.html

### Overview

DeepStream is NVIDIA's production-grade SDK for AI-powered video analytics. More complex than jetson-inference, but more powerful for production deployments.

### Features

- **Multi-stream processing** - Handle multiple camera feeds simultaneously
- **Hardware-accelerated pipelines** - GStreamer with CUDA acceleration
- **RTSP/WebRTC output** - Stream to web browsers
- **Docker support** - `deepstream-l4t` container for Jetson
- **Production-ready** - Used in commercial surveillance and analytics products

### Quick Start

```bash
# Pull DeepStream container
docker pull nvcr.io/nvidia/deepstream-l4t:7.0-samples-multiarch

# Run with camera access
docker run -it --rm --net=host --runtime nvidia \
  -e DISPLAY=$DISPLAY \
  --device /dev/video0:/dev/video0 \
  -v /tmp/.X11-unix/:/tmp/.X11-unix \
  nvcr.io/nvidia/deepstream-l4t:7.0-samples-multiarch
```

### Web Browser Streaming

DeepStream supports RTSP output that can be:
1. Viewed directly with RTSP player (VLC, etc.)
2. Converted to WebRTC for native browser support
3. Transcoded to HLS/DASH for web streaming

Configuration example:
```ini
[sink2]
enable=1
type=4          # RTSP
rtsp-port=8554
udp-port=5400
```

### Relevance to Our Demo

**Good for**:
- Production deployment (future)
- Multiple camera feeds
- Complex video analytics pipelines
- RTSP streaming to web

**May be overkill for**:
- Simple face detection demo
- Single camera feed
- Rapid prototyping

---

## 🛠️ Supporting: dusty-nv/jetson-containers

**Repository**: https://github.com/dusty-nv/jetson-containers

### Overview

Modular container build system with 300+ pre-built containers for AI/ML on Jetson. Includes OpenCV, PyTorch, TensorFlow, ROS, and more.

### Features

- **Pre-built OpenCV** with CUDA support
- **Hardware acceleration** examples
- **Automated builds** for different JetPack versions
- **Mix and match** containers for your needs

### Quick Start

```bash
# Install container tools
git clone https://github.com/dusty-nv/jetson-containers
bash jetson-containers/install.sh

# Run OpenCV container with camera
jetson-containers run $(autotag opencv)
```

### OpenCV CUDA Example

```python
import cv2

# Upload image to GPU
gpu_img = cv2.cuda_GpuMat()
gpu_img.upload(cpu_img)

# GPU-accelerated resize
gpu_resized = cv2.cuda.resize(gpu_img, (640, 480))

# Download back to CPU
cpu_result = gpu_resized.download()
```

### Relevance to Our Demo

**Perfect for**:
- Custom Docker builds with specific packages
- Understanding Jetson container best practices
- OpenCV with CUDA acceleration
- Building on top of proven base images

---

## 🎓 Official NVIDIA Tutorials

### Your First Jetson Container

**URL**: https://developer.nvidia.com/embedded/learn/tutorials/jetson-container

Step-by-step guide to creating your first Jetson Docker container.

### NVIDIA Container Runtime on Jetson

**URL**: https://nvidia.github.io/container-wiki/toolkit/jetson.html

Technical documentation on how the NVIDIA container runtime works on Jetson devices.

### Jetson AI Fundamentals

**URL**: https://developer.nvidia.com/embedded/learn/tutorials

Official tutorial series covering DNN training, inference, and deployment on Jetson.

---

## 📝 Key Takeaways for Our Camera Demo

### Docker Best Practices on Jetson

1. **Base Image**: Use `nvcr.io/nvidia/l4t-base` or `dustynv/jetson-inference`
2. **Runtime**: Use `--runtime nvidia` to enable GPU access
3. **Camera Device**: Mount with `--device /dev/video0:/dev/video0`
4. **Display**: For testing, mount `-v /tmp/.X11-unix/:/tmp/.X11-unix -e DISPLAY=$DISPLAY`
5. **Network**: Use `--net=host` for simplicity with streaming

### Hardware Acceleration

1. **OpenCV CUDA**: Install `opencv-python` with CUDA support (pre-built in jetson containers)
2. **TensorRT**: For DNN inference optimization
3. **GStreamer**: For hardware-accelerated video encode/decode
4. **VPI (Vision Programming Interface)**: NVIDIA's accelerated vision library

### Camera Access

1. **V4L2 (USB webcam)**: `/dev/video0`, `/dev/video1`, etc.
2. **MIPI CSI**: Use `nvarguscamerasrc` GStreamer plugin
3. **Permissions**: Ensure user is in `video` group

### Web Streaming Options

1. **MJPEG**: Simplest, works everywhere (our current choice)
2. **RTSP**: Better quality, needs player or transcoding
3. **WebRTC**: Native browser support, more complex setup
4. **HLS/DASH**: For scalable streaming, higher latency

---

## 🎯 Recommendation for Our Demo

### Phase 1: Current Implementation (Python + Flask + MJPEG)
Keep our current approach for rapid prototyping. It works well and is simple for the robotics team to understand.

### Phase 2: Hardware Acceleration (After Demo Works)
Consider switching to `dusty-nv/jetson-inference` base image and using their camera utilities:

```dockerfile
FROM dustynv/jetson-inference:r36.2.0

# Add our Flask/SocketIO requirements
COPY requirements.txt .
RUN pip3 install -r requirements.txt

# Copy our application
COPY . /app
WORKDIR /app

EXPOSE 5500
CMD ["python3", "app.py"]
```

Benefits:
- Hardware-accelerated video processing
- Proven camera device mounting
- Can use their utilities for capture/streaming
- Still use our Flask/SocketIO architecture

### Phase 3: Production Optimization (Future)
If performance becomes critical:
- Migrate to DeepStream for multi-camera support
- Use GStreamer pipelines for hardware encode/decode
- Add WebRTC for better web streaming
- Optimize with TensorRT for DNN inference

---

## 📚 Additional Resources

### Community Examples

1. **RidgeRun Jetson AI**: https://developer.ridgerun.com/wiki/index.php/NVIDIA_Jetson_Reference_Designs
   - OpenSource Docker project with ML/AI examples
   - DeepStream, OpenCV, GStreamer, GstInference

2. **Jetson Hacks**: https://jetsonhacks.com/
   - Community tutorials and examples
   - Container setup guides

3. **NVIDIA Developer Forums**: https://forums.developer.nvidia.com/c/agx-autonomous-machines/jetson-embedded-systems/
   - Active community support
   - Real-world examples and troubleshooting

### Tools

1. **jetson-stats**: Monitor GPU/CPU/memory usage
   ```bash
   sudo pip3 install jetson-stats
   jtop
   ```

2. **jtop Docker**: Monitor from inside containers
   ```bash
   docker run --runtime nvidia -it --rm --pid=host dustynv/jetson-stats
   ```

---

## 🔗 Quick Links Summary

| Resource | Best For | URL |
|----------|----------|-----|
| **jetson-inference** | Getting started, camera examples | https://github.com/dusty-nv/jetson-inference |
| **jetson-containers** | Pre-built ML containers | https://github.com/dusty-nv/jetson-containers |
| **DeepStream** | Production video analytics | https://github.com/NVIDIA-AI-IOT/deepstream_dockers |
| **NVIDIA Tutorials** | Official learning path | https://developer.nvidia.com/embedded/learn/tutorials |
| **Container Runtime** | Technical reference | https://nvidia.github.io/container-wiki/toolkit/jetson.html |

---

## 🚀 Next Steps

1. **Implement current demo** (Python + Flask + MJPEG) on AGX1
2. **Test performance** and measure latency/FPS
3. **If performance sufficient**: Keep current approach
4. **If performance insufficient**: Migrate to jetson-inference base image
5. **Share findings** with robotics team for their implementation decisions

---

**Document Created**: 2025-10-20
**Purpose**: Provide NVIDIA reference implementations for Camera demo project
**Status**: Ready for implementation reference
