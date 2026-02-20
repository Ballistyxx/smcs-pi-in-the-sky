#!/bin/bash
# Startup script for SMCS Pi in the Sky

echo "🚀 Starting SMCS Pi in the Sky..."

# Check if system packages are installed
echo "📦 Checking system dependencies..."
MISSING_PACKAGES=()

if ! dpkg -l | grep -q "python3-picamera2"; then
    MISSING_PACKAGES+=("python3-picamera2")
fi

if ! dpkg -l | grep -q "python3-pigpio"; then
    MISSING_PACKAGES+=("python3-pigpio")
fi

if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "⚠️  Missing system packages: ${MISSING_PACKAGES[*]}"
    echo "Installing required system packages..."
    sudo apt update
    sudo apt install -y "${MISSING_PACKAGES[@]}"
fi

# Check if pigpiod is running
if ! pgrep -x "pigpiod" > /dev/null; then
    echo "⚠️  pigpiod is not running. Starting it now..."
    sudo pigpiod
    sleep 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment with system site packages..."
    python3 -m venv --system-site-packages venv
else
    # Check if existing venv has system-site-packages
    if [ ! -f "venv/pyvenv.cfg" ] || ! grep -q "include-system-site-packages = true" venv/pyvenv.cfg; then
        echo "⚠️  Existing venv doesn't have system-site-packages. Recreating..."
        rm -rf venv
        python3 -m venv --system-site-packages venv
    fi
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "📥 Installing Python dependencies..."
pip install -q -r requirements.txt

# Start the application
echo "✅ Starting Flask application..."
echo "🌐 Dashboard will be available at: http://$(hostname -I | awk '{print $1}'):5000/admin/dashboard"
echo "📡 API endpoint available at: http://$(hostname -I | awk '{print $1}'):5000/api/coordinate"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python3 app.py
