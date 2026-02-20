# SMCS Pi in the Sky

A Raspberry Pi 4 camera streaming application with servo motor control and brightest pixel detection.

## Features

- **Live Video Streaming**: MJPEG stream accessible at `/admin/stream` or `/admin/stream.mjpeg`
- **Brightest Pixel Detection**: Real-time tracking of the brightest point in the camera feed
- **Servo Control**: Web-based dashboard for controlling two SM-S4303R continuous rotation servos
- **Authentication**: Admin pages protected with basic HTTP authentication
- **Public API**: Unauthenticated endpoint for brightest pixel coordinates

## Hardware Requirements

- Raspberry Pi 4
- OV5647 Camera Module (connected via MIPI interface)
- 2x SM-S4303R Continuous Rotation Servos
  - Servo 1: GPIO 17
  - Servo 2: GPIO 27
- Power supply for servos

## Software Requirements

- Raspberry Pi OS (Debian Trixie)
- Python 3.9+
- pigpiod daemon (for servo control)

## Installation

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install pigpio daemon
sudo apt install pigpio python3-pigpio -y

# Enable and start pigpiod
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### 2. Set Up Python Environment

```bash
# Navigate to project directory
cd /path/to/smcs-pi-in-the-sky

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### 3. Configure Authentication

The `.env` file contains the login credentials in the format:
```
ADMIN_USERNAME=username
ADMIN_PASSWORD=password
```
*These are not the actual admin credentials.
You can modify these in the `.env` file if needed.

## Usage

### Starting the Application

```bash
# Make sure pigpiod is running
sudo systemctl status pigpiod

# Activate virtual environment
source venv/bin/activate

# Run the application
python3 app.py
```

The server will start on `http://0.0.0.0:5000`

### Accessing the Dashboard

1. Open a web browser
2. Navigate to `http://<raspberry-pi-ip>:5000/admin/dashboard`
3. Enter credentials when prompted

## API Endpoints

### Public Endpoints (No Authentication Required)

- **GET** `/api/coordinate`
  - Returns the (x, y) coordinates of the brightest pixel
  - Example response: `{"x": 320, "y": 240}`

### Admin Endpoints (Authentication Required)

- **GET** `/admin/dashboard`
  - Web dashboard with video stream and servo controls

- **GET** `/admin/stream` or `/admin/stream.mjpeg`
  - MJPEG video stream from camera

- **POST** `/admin/servo/control`
  - Control servo motors
  - Request body:
    ```json
    {
      "servo": "servo1",  // or "servo2"
      "pulse_width": 1500  // 500-2500 microseconds
    }
    ```

- **POST** `/admin/servo/stop`
  - Stop a servo motor
  - Request body:
    ```json
    {
      "servo": "servo1"  // or "servo2"
    }
    ```

## Servo Control Guide

The SM-S4303R servos are continuous rotation servos:

- **1500 μs**: Stop/Rest position
- **< 1500 μs**: Clockwise rotation (speed increases as value decreases)
- **> 1500 μs**: Counter-clockwise rotation (speed increases as value increases)
- **Range**: 500-2500 microseconds

## Project Structure

```
smcs-pi-in-the-sky/
├── app.py                 # Main Flask application
├── camera.py             # Camera management and image processing
├── servo_control.py      # Servo motor control using pigpiod
├── templates/
│   └── dashboard.html    # Admin dashboard interface
├── .env                  # Authentication credentials (not in git)
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Troubleshooting

### Camera Not Starting

```bash
# Check if camera is detected
rpicam-vid --list-cameras

# Check camera interface is enabled
sudo raspi-config
# Navigate to Interface Options > Camera and enable it
```

### Servos Not Responding

```bash
# Check if pigpiod is running
sudo systemctl status pigpiod

# Restart pigpiod if needed
sudo systemctl restart pigpiod

# Check GPIO permissions
sudo usermod -a -G gpio $USER
```

### Permission Errors

```bash
# Add user to video group for camera access
sudo usermod -a -G video $USER

# Log out and back in for changes to take effect
```

## Development

To run in development mode with debug enabled, modify `app.py`:

```python
app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
```

## Security Notes

- Authentication credentials are stored in plain text in `.env`
- The API endpoint `/api/coordinate` is intentionally public
- For production use, consider implementing HTTPS and more robust authentication
- Never commit `.env` to version control

## License

This project is created for educational purposes under the MIT license.
Made by Eli Ferrara, SMCS class of 2026.
