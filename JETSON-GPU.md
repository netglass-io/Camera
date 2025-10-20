# NVIDIA Jetson GPU Configuration for Docker

## Critical Information

**⚠️ THIS IS IMPORTANT - Read This Before Building Containers ⚠️**

This document explains how to properly configure Docker containers to use the NVIDIA GPU on Jetson devices. **This has confused many developers in the past**, so please read carefully.

---

## The Problem

On NVIDIA Jetson devices (AGX Orin, Xavier, Nano, etc.), Docker containers **DO NOT automatically have GPU access**. Without proper configuration:

- ❌ CUDA will not work
- ❌ TensorRT will fail
- ❌ cuDNN operations will fail
- ❌ GPU-accelerated OpenCV functions will fall back to CPU
- ❌ Any ML inference using GPU will crash or be extremely slow

## The Solution

### In docker-compose.yml

You **MUST** add `runtime: nvidia` to your service definition:

```yaml
services:
  camera-demo:
    runtime: nvidia  # ← THIS IS CRITICAL!
    # ... rest of configuration
```

### Complete Example

```yaml
version: '3.8'

services:
  camera-demo:
    build:
      context: .
      dockerfile: Dockerfile
    container_name: camera-demo

    # ========================================
    # CRITICAL: NVIDIA GPU runtime
    # ========================================
    runtime: nvidia

    # Optional but recommended GPU environment variables
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all

    # ... rest of configuration
```

---

## How to Verify GPU Access

### 1. Check if NVIDIA Runtime is Available

```bash
docker info | grep -i runtime
```

Expected output should include `nvidia` in the list of runtimes.

### 2. Test GPU Access in Container

```bash
# Start your container
docker compose up -d

# Enter container
docker exec -it camera-demo bash

# Check if GPU is visible (if nvidia-smi is installed)
nvidia-smi

# Or check CUDA devices with Python
python3 -c "import cv2; print(cv2.cuda.getCudaEnabledDeviceCount())"
```

Expected: Device count > 0

### 3. Inspect Running Container

```bash
# Check runtime setting
docker inspect camera-demo | grep -i runtime
```

Expected output: `"Runtime": "nvidia"`

---

## Common Mistakes

### ❌ Mistake #1: Forgetting runtime: nvidia

```yaml
services:
  my-service:
    image: my-image
    # Missing: runtime: nvidia
```

**Result**: GPU not accessible, everything runs on CPU

### ❌ Mistake #2: Using docker run without --runtime

```bash
# Wrong:
docker run -it my-image

# Correct:
docker run --runtime nvidia -it my-image
```

### ❌ Mistake #3: Assuming GPU "just works"

Many developers assume that because the host has a GPU, Docker containers will automatically have access. **This is false** on Jetson devices.

---

## Why This Setting Exists

The `runtime: nvidia` setting tells Docker to:

1. Use the NVIDIA Container Runtime instead of the default `runc`
2. Mount NVIDIA driver libraries into the container
3. Configure device access for CUDA operations
4. Set up proper cgroups for GPU memory management

Without this, the container is completely isolated from the GPU hardware.

---

## Environment Variables Explained

### NVIDIA_VISIBLE_DEVICES

Controls which GPUs are visible to the container.

- `all` - All GPUs are visible (default for Jetson, usually only 1 GPU)
- `0` - Only GPU 0 is visible
- `none` - No GPUs visible

**Recommendation**: Use `all` on Jetson devices (they typically have only one GPU).

### NVIDIA_DRIVER_CAPABILITIES

Controls which NVIDIA driver capabilities are enabled.

- `all` - All capabilities (compute, graphics, video, etc.)
- `compute,utility` - Only CUDA compute and nvidia-smi
- `graphics,display` - Graphics and display capabilities

**Recommendation**: Use `all` unless you have specific restrictions.

---

## Verification on AGX1

This configuration has been verified on `agx1.simula.io` by inspecting the `riva-speech` container:

```bash
$ docker inspect riva-speech | grep Runtime
            "Runtime": "nvidia",
```

The `riva-speech` container successfully uses GPU for AI inference, confirming this configuration works.

---

## Quick Reference for Different Scenarios

### Scenario 1: docker-compose (Recommended)

```yaml
services:
  my-service:
    runtime: nvidia
    environment:
      - NVIDIA_VISIBLE_DEVICES=all
      - NVIDIA_DRIVER_CAPABILITIES=all
```

### Scenario 2: docker run

```bash
docker run \
  --runtime nvidia \
  -e NVIDIA_VISIBLE_DEVICES=all \
  -e NVIDIA_DRIVER_CAPABILITIES=all \
  my-image
```

### Scenario 3: Dockerfile

No special configuration needed in Dockerfile. The runtime is configured at **container runtime**, not build time.

---

## Testing GPU Access with Python

Create a simple test script to verify GPU access:

```python
import cv2

# Check CUDA-enabled devices
cuda_devices = cv2.cuda.getCudaEnabledDeviceCount()
print(f"CUDA-enabled devices: {cuda_devices}")

if cuda_devices > 0:
    print("✅ GPU is accessible!")
    print(f"Device name: {cv2.cuda.getDevice()}")
else:
    print("❌ No GPU detected - check runtime: nvidia setting")
```

---

## Troubleshooting

### Problem: "CUDA not available" or "0 CUDA devices"

**Solution**:
1. Verify `runtime: nvidia` is in docker-compose.yml
2. Rebuild and restart container: `docker compose down && docker compose up -d`
3. Check `docker inspect <container> | grep Runtime`

### Problem: "Unknown runtime specified nvidia"

**Cause**: NVIDIA Container Runtime not installed on host

**Solution**:
```bash
# Check if nvidia runtime exists
docker info | grep -i runtime

# If missing, install nvidia-container-runtime
# (This should already be installed on Jetson devices)
sudo apt-get install nvidia-container-runtime
```

### Problem: Container starts but GPU operations still fail

**Possible causes**:
1. NVIDIA driver version mismatch
2. CUDA version incompatibility between host and container
3. Missing CUDA libraries in container image

**Solution**: Use NVIDIA's official L4T base images for Jetson:
```dockerfile
FROM nvcr.io/nvidia/l4t-base:r35.4.1
```

---

## Additional Resources

### Official NVIDIA Documentation

- **🌟 NVIDIA Jetson Container Tutorial** (START HERE): https://developer.nvidia.com/embedded/learn/tutorials/jetson-container
  - Official tutorial explaining container fundamentals on Jetson
  - Shows correct usage of `--runtime nvidia` flag
  - Covers docker pull, run, and image management
  - **This is the authoritative source from NVIDIA**

### Community Resources

- **NVIDIA Container Toolkit**: https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/
- **Jetson Containers**: https://github.com/dusty-nv/jetson-containers
- **L4T Container Docs**: https://catalog.ngc.nvidia.com/orgs/nvidia/containers/l4t-base
- **NGC Jetson Cloud-Native**: https://ngc.nvidia.com/ (Search for "Jetson" for pre-tested containers)

---

## Summary Checklist

Before deploying any GPU-dependent container on Jetson:

- [ ] `runtime: nvidia` is set in docker-compose.yml
- [ ] `NVIDIA_VISIBLE_DEVICES=all` is in environment variables
- [ ] `NVIDIA_DRIVER_CAPABILITIES=all` is in environment variables
- [ ] Container has been rebuilt after changes
- [ ] GPU access verified with test script

---

**Document Created**: 2025-10-20
**Verified On**: AGX1 Jetson AGX Orin
**Reference Container**: riva-speech (nvcr.io/nvidia/riva/riva-speech:2.19.0-l4t-aarch64)
**Status**: Production-verified configuration

---

## For Future Developers

If you're reading this because GPU isn't working:

1. Check if `runtime: nvidia` is in your docker-compose.yml
2. If it's missing, add it
3. Run `docker compose down && docker compose up -d`
4. Test with the Python script above
5. If still not working, check the troubleshooting section

**This simple setting solves 95% of GPU issues on Jetson devices.**
