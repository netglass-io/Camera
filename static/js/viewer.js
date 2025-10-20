/**
 * Camera Viewer - SocketIO Client
 * Handles real-time communication with camera processing backend
 */

// Initialize SocketIO connection
const socket = io();

// Connection status tracking
let isConnected = false;
let lastFrameNumber = 0;

/**
 * Connection Event Handlers
 */
socket.on('connect', () => {
    console.log('Connected to camera service');
    isConnected = true;
    updateConnectionStatus('connected');
    showStatusMessage('Connected to camera service', 'success');
});

socket.on('disconnect', () => {
    console.log('Disconnected from camera service');
    isConnected = false;
    updateConnectionStatus('disconnected');
    showStatusMessage('Disconnected from camera service', 'warning');
});

socket.on('connect_error', (error) => {
    console.error('Connection error:', error);
    updateConnectionStatus('error');
    showStatusMessage('Connection error', 'danger');
});

/**
 * Camera Metadata Handler
 * Receives face detection data and updates UI
 */
socket.on('camera_metadata', (data) => {
    // Update face count
    document.getElementById('face-count').textContent = data.face_count;

    // Update FPS
    document.getElementById('fps').textContent = data.fps;

    // Update frame number
    document.getElementById('frame-number').textContent = data.frame_number;
    lastFrameNumber = data.frame_number;

    // Log face coordinates (for debugging)
    if (data.faces && data.faces.length > 0) {
        console.log(`Detected ${data.faces.length} face(s):`, data.faces);
    }
});

/**
 * Performance Metrics Handler
 * Receives processing time data and updates UI
 */
socket.on('performance_metrics', (data) => {
    // Update processing time
    document.getElementById('processing-time').textContent = data.processing_time_ms.toFixed(1);

    // Update detection time
    document.getElementById('detection-time').textContent = data.detection_time_ms.toFixed(1);

    // Color-code based on performance
    const processingElement = document.getElementById('processing-time');
    if (data.processing_time_ms > 50) {
        processingElement.style.color = '#e74c3c'; // Red for slow
    } else if (data.processing_time_ms > 30) {
        processingElement.style.color = '#f39c12'; // Orange for moderate
    } else {
        processingElement.style.color = '#27ae60'; // Green for fast
    }
});

/**
 * Status Update Handler
 * Receives status updates from server
 */
socket.on('status', (data) => {
    console.log('Status update:', data);

    // Update system info if present
    if (data.camera_resolution) {
        document.getElementById('camera-resolution').textContent = data.camera_resolution;
    }

    if (data.target_fps) {
        document.getElementById('target-fps').textContent = data.target_fps;
    }

    if (data.detection_enabled !== undefined) {
        // Update detection toggle if it differs from current state
        const toggle = document.getElementById('toggle-detection');
        if (toggle.checked !== data.detection_enabled) {
            toggle.checked = data.detection_enabled;
        }

        // Update system status
        const statusBadge = document.getElementById('system-status');
        if (data.detection_enabled) {
            statusBadge.textContent = 'Detecting';
            statusBadge.className = 'badge bg-success';
        } else {
            statusBadge.textContent = 'Idle';
            statusBadge.className = 'badge bg-secondary';
        }
    }

    // Show status message if present
    if (data.message) {
        showStatusMessage(data.message, 'info');
    }
});

/**
 * Control Functions
 */

function toggleDetection() {
    const enabled = document.getElementById('toggle-detection').checked;
    socket.emit('toggle_detection', { enabled: enabled });
    console.log(`Detection ${enabled ? 'enabled' : 'disabled'}`);
}

function setSensitivity(value) {
    document.getElementById('sensitivity-value').textContent = value;
    socket.emit('set_sensitivity', { threshold: parseFloat(value) });
    console.log(`Sensitivity set to: ${value}`);
}

function captureSnapshot() {
    socket.emit('capture_snapshot');
    showStatusMessage('Snapshot captured', 'info');
    console.log('Snapshot requested');
}

function resetCalibration() {
    socket.emit('reset_calibration');
    showStatusMessage('Calibration reset', 'info');
    console.log('Calibration reset requested');
}

/**
 * UI Helper Functions
 */

function updateConnectionStatus(status) {
    const statusElement = document.getElementById('connection-status');
    const badge = statusElement.querySelector('.badge');

    switch (status) {
        case 'connected':
            badge.textContent = 'Connected';
            badge.className = 'badge bg-success';
            break;
        case 'disconnected':
            badge.textContent = 'Disconnected';
            badge.className = 'badge bg-warning';
            break;
        case 'error':
            badge.textContent = 'Error';
            badge.className = 'badge bg-danger';
            break;
        default:
            badge.textContent = 'Unknown';
            badge.className = 'badge bg-secondary';
    }
}

function showStatusMessage(message, type = 'info') {
    const container = document.getElementById('status-messages');

    // Create alert element
    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.role = 'alert';
    alert.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
    `;

    // Add to container
    container.appendChild(alert);

    // Auto-dismiss after 5 seconds
    setTimeout(() => {
        alert.classList.remove('show');
        setTimeout(() => alert.remove(), 150);
    }, 5000);
}

/**
 * Performance Monitoring
 * Check for stream health
 */
let lastHealthCheck = Date.now();
setInterval(() => {
    const now = Date.now();
    const elapsed = now - lastHealthCheck;

    // If we haven't received frames in 5 seconds, show warning
    if (elapsed > 5000 && isConnected) {
        console.warn('No frames received in 5 seconds');
        showStatusMessage('Stream may be stalled', 'warning');
    }

    lastHealthCheck = now;
}, 5000);

/**
 * Initialize UI on page load
 */
document.addEventListener('DOMContentLoaded', () => {
    console.log('Camera viewer initialized');

    // Set initial sensitivity display
    const sensitivitySlider = document.getElementById('sensitivity-slider');
    document.getElementById('sensitivity-value').textContent = sensitivitySlider.value;

    // Add error handler for video stream
    const videoStream = document.getElementById('video-stream');
    videoStream.onerror = () => {
        console.error('Error loading video stream');
        showStatusMessage('Error loading video stream', 'danger');
    };

    console.log('UI initialized, waiting for connection...');
});
