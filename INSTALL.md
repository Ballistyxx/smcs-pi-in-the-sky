# Installation Guide for Raspberry Pi

## Quick Install (Recommended)

Just run the startup script - it will check and install everything automatically:

```bash
cd /home/smcspi/smcs-pi-in-the-sky
./start.sh
```

The script will automatically:
1. Check for and install missing system packages
2. Start pigpiod if not running
3. Create a virtual environment with system site packages
4. Install Python dependencies
5. Start the Flask server

---

## Manual Installation (If Needed)

If you prefer to install manually or troubleshoot issues:

### 1. Install System Dependencies

```bash
# Update package list
sudo apt update

# Install required system packages
sudo apt install -y python3-picamera2 python3-pigpio python3-venv

# Enable and start pigpiod service
sudo systemctl enable pigpiod
sudo systemctl start pigpiod

# Verify pigpiod is running
sudo systemctl status pigpiod
```

### 2. Create Virtual Environment

**IMPORTANT**: Use `--system-site-packages` flag to access system-installed picamera2:

```bash
cd /home/smcspi/smcs-pi-in-the-sky
python3 -m venv --system-site-packages venv
```

### 3. Install Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt
```

### 4. Run the Application

```bash
python3 app.py
```

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'libcamera'"

**Cause**: picamera2 needs to be installed at system level, not via pip.

**Solution**:
```bash
# Install system package
sudo apt install python3-picamera2

# Recreate venv with system-site-packages
rm -rf venv
python3 -m venv --system-site-packages venv
source venv/bin/activate
pip install -r requirements.txt
```

### Error: pigpio related errors

**Cause**: pigpiod daemon not running or not installed.

**Solution**:
```bash
# Install pigpio
sudo apt install python3-pigpio

# Start pigpiod
sudo pigpiod

# Or enable as service
sudo systemctl enable pigpiod
sudo systemctl start pigpiod
```

### Camera Not Detected

**Check camera connection**:
```bash
rpicam-vid --list-cameras
```

**Enable camera interface**:
```bash
sudo raspi-config
# Navigate to: Interface Options > Camera > Enable
```

### Permission Issues

**Add user to required groups**:
```bash
sudo usermod -a -G video,gpio $USER
# Log out and back in for changes to take effect
```

---

## Why System Packages?

On Raspberry Pi OS, some packages must be installed system-wide because they:
- Depend on hardware-specific libraries (libcamera)
- Need low-level system access (pigpio)
- Are pre-compiled for ARM architecture

These packages are:
- `python3-picamera2` - Camera interface with libcamera bindings
- `python3-pigpio` - GPIO control library

The virtual environment uses `--system-site-packages` to access these while keeping other dependencies isolated.

---

## Verifying Installation

After installation, verify all components:

```bash
# Check Python packages
source venv/bin/activate
python3 -c "import picamera2; print('picamera2 OK')"
python3 -c "import pigpio; print('pigpio OK')"
python3 -c "import flask; print('flask OK')"

# Check pigpiod
pgrep pigpiod && echo "pigpiod running" || echo "pigpiod NOT running"

# Check camera
rpicam-vid --list-cameras
```

All should complete without errors.
