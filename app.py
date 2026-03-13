#!/usr/bin/env python3
"""
SMCS Pi in the Sky - Main Flask Application
Raspberry Pi 4 camera streaming with servo control
"""
import os
from functools import wraps
from flask import Flask, Response, render_template, request, jsonify
from dotenv import load_dotenv
from camera import CameraManager
from servo_control import ServoController

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.urandom(24)

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
    """Generator function to stream video frames to a single client.
    Blocks on each iteration until the broadcaster has a new frame ready."""
    while True:
        frame = camera_manager.get_jpeg_frame()
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


# Public API endpoint - no authentication required
@app.route('/api/coordinate', methods=['GET'])
def get_coordinate():
    """Return the coordinates of the brightest pixel."""
    return jsonify(camera_manager.get_brightest_pixel())


# Public stream endpoints - no authentication required
@app.route('/admin/stream')
@app.route('/admin/stream.mjpeg')
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
    camera_manager.start()
    try:
        app.run(host='0.0.0.0', port=5000, threaded=True)
    finally:
        camera_manager.stop()
        servo_controller.cleanup()
