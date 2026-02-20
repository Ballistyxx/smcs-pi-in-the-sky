#!/usr/bin/env python3
"""
SMCS Pi in the Sky - Main Flask Application
Raspberry Pi 4 camera streaming with servo control
"""
import os
import io
import time
from functools import wraps
from threading import Lock
from flask import Flask, Response, render_template, request, jsonify, session
from dotenv import load_dotenv
from camera import CameraManager
from servo_control import ServoController

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Random secret key for sessions

# Configuration from .env
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD')

# Validate that credentials are configured
if not ADMIN_USERNAME or not ADMIN_PASSWORD:
    raise ValueError(
        "ADMIN_USERNAME and ADMIN_PASSWORD must be set in .env file. "
        "See .env for configuration."
    )

# Initialize camera and servo controller
camera_manager = CameraManager()
servo_controller = ServoController()

# Lock for thread safety
coordinate_lock = Lock()
latest_coordinate = {'x': 0, 'y': 0}


def check_auth(username, password):
    """Check if username/password combination is valid."""
    return username == ADMIN_USERNAME and password == ADMIN_PASSWORD


def requires_auth(f):
    """Decorator for routes that require authentication."""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return Response(
                'Authentication required',
                401,
                {'WWW-Authenticate': 'Basic realm="Admin Area"'}
            )
        return f(*args, **kwargs)
    return decorated


def generate_frames():
    """Generator function to stream video frames."""
    while True:
        frame_data = camera_manager.get_frame()
        if frame_data:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_data + b'\r\n')
        time.sleep(0.033)  # ~30 fps


def update_brightest_pixel():
    """Background task to continuously update brightest pixel coordinate."""
    global latest_coordinate
    while True:
        coord = camera_manager.get_brightest_pixel()
        if coord:
            with coordinate_lock:
                latest_coordinate = coord
        time.sleep(0.05)  # Update at ~20Hz


# Public API endpoint - no authentication required
@app.route('/api/coordinate', methods=['GET'])
def get_coordinate():
    """Return the coordinates of the brightest pixel."""
    with coordinate_lock:
        return jsonify(latest_coordinate)


# Admin endpoints - authentication required
@app.route('/admin/stream')
@app.route('/admin/stream.mjpeg')
@requires_auth
def video_stream():
    """Video streaming route."""
    return Response(
        generate_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame'
    )


@app.route('/admin/dashboard')
@requires_auth
def dashboard():
    """Render the admin dashboard."""
    return render_template('dashboard.html')


@app.route('/admin/servo/control', methods=['POST'])
@requires_auth
def control_servo():
    """Control servo motors."""
    try:
        data = request.json
        servo_id = data.get('servo')  # 'servo1' (GPIO17) or 'servo2' (GPIO27)
        pulse_width = data.get('pulse_width')  # Pulse width in microseconds

        if servo_id not in ['servo1', 'servo2']:
            return jsonify({'error': 'Invalid servo ID'}), 400

        if pulse_width is None or not (500 <= pulse_width <= 2500):
            return jsonify({'error': 'Invalid pulse width (500-2500 us)'}), 400

        gpio_pin = 17 if servo_id == 'servo1' else 27
        servo_controller.set_servo(gpio_pin, pulse_width)

        return jsonify({
            'success': True,
            'servo': servo_id,
            'gpio': gpio_pin,
            'pulse_width': pulse_width
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/admin/servo/stop', methods=['POST'])
@requires_auth
def stop_servo():
    """Stop a servo motor."""
    try:
        data = request.json
        servo_id = data.get('servo')

        if servo_id not in ['servo1', 'servo2']:
            return jsonify({'error': 'Invalid servo ID'}), 400

        gpio_pin = 17 if servo_id == 'servo1' else 27
        servo_controller.stop_servo(gpio_pin)

        return jsonify({
            'success': True,
            'servo': servo_id,
            'gpio': gpio_pin,
            'stopped': True
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/')
def index():
    """Root endpoint - redirect to API documentation."""
    return jsonify({
        'message': 'SMCS Pi in the Sky API',
        'endpoints': {
            'public': {
                '/api/coordinate': 'GET - Returns brightest pixel coordinates'
            },
            'admin': {
                '/admin/dashboard': 'GET - Admin dashboard (requires auth)',
                '/admin/stream': 'GET - Video stream (requires auth)',
                '/admin/stream.mjpeg': 'GET - Video stream (requires auth)',
                '/admin/servo/control': 'POST - Control servos (requires auth)',
                '/admin/servo/stop': 'POST - Stop servos (requires auth)'
            }
        }
    })


if __name__ == '__main__':
    # Start camera
    camera_manager.start()

    # Start coordinate update thread
    import threading
    coord_thread = threading.Thread(target=update_brightest_pixel, daemon=True)
    coord_thread.start()

    # Run Flask app
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        camera_manager.stop()
        servo_controller.cleanup()
