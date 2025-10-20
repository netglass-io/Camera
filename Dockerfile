# Camera Processing Demo - Dockerfile
# Base image: Python 3.11 slim (lightweight)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OpenCV
# libgl1: OpenGL support
# libglib2.0-0: GLib library
# libsm6, libxext6, libxrender-dev: X11 dependencies
# v4l-utils: Video4Linux utilities for camera access
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    v4l-utils \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY app.py .
COPY static/ ./static/
COPY templates/ ./templates/

# Expose port 5500
EXPOSE 5500

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5500/').read()" || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV CAMERA_DEVICE=/dev/video0
ENV TARGET_FPS=30

# Run application
CMD ["python", "app.py"]
