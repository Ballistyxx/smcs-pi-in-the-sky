#!/usr/bin/env python3
"""
Camera management and image processing module
Handles video streaming and brightest pixel detection
"""
import io
import time
import numpy as np
from PIL import Image
from picamera2 import Picamera2
from threading import Lock


class CameraManager:
    """Manages camera operations and image processing."""

    def __init__(self):
        """Initialize the camera manager."""
        self.camera = None
        self.lock = Lock()
        self.latest_frame = None
        self.is_running = False

    def start(self):
        """Start the camera."""
        if self.is_running:
            return

        try:
            self.camera = Picamera2()

            # Configure camera for video streaming
            # Using 640x480 mode for better performance
            config = self.camera.create_video_configuration(
                main={"size": (640, 480), "format": "RGB888"},
                controls={"FrameRate": 30}
            )
            self.camera.configure(config)
            self.camera.start()

            # Give camera time to warm up
            time.sleep(2)
            self.is_running = True
            print("Camera started successfully")
        except Exception as e:
            print(f"Error starting camera: {e}")
            raise

    def stop(self):
        """Stop the camera."""
        if self.camera and self.is_running:
            self.camera.stop()
            self.is_running = False
            print("Camera stopped")

    def get_frame(self):
        """
        Capture a frame and return it as JPEG bytes.

        Returns:
            bytes: JPEG encoded frame
        """
        if not self.is_running:
            return None

        try:
            with self.lock:
                # Capture frame as numpy array
                frame = self.camera.capture_array()

                # Store for brightest pixel detection
                self.latest_frame = frame.copy()

                # Convert to PIL Image
                image = Image.fromarray(frame)

                # Encode as JPEG
                buffer = io.BytesIO()
                image.save(buffer, format='JPEG', quality=85)
                return buffer.getvalue()
        except Exception as e:
            print(f"Error capturing frame: {e}")
            return None

    def get_brightest_pixel(self):
        """
        Find the brightest pixel in the current frame.

        Returns:
            dict: {'x': int, 'y': int} coordinates of brightest pixel
        """
        if self.latest_frame is None:
            return {'x': 0, 'y': 0}

        try:
            with self.lock:
                frame = self.latest_frame.copy()

            # Convert RGB to grayscale (simple average method)
            # This gives us brightness values
            if len(frame.shape) == 3:
                # RGB frame - calculate brightness
                gray = np.mean(frame, axis=2)
            else:
                # Already grayscale
                gray = frame

            # Find the coordinates of the maximum value
            max_idx = np.argmax(gray)
            y, x = np.unravel_index(max_idx, gray.shape)

            return {
                'x': int(x),
                'y': int(y)
            }
        except Exception as e:
            print(f"Error detecting brightest pixel: {e}")
            return {'x': 0, 'y': 0}
