#!/usr/bin/env python3
"""
Camera management and image processing module
Handles video streaming and brightest pixel detection
"""
import io
import time
import threading
import numpy as np
from PIL import Image
from picamera2 import Picamera2


class CameraManager:
    """Manages camera operations and image processing."""

    def __init__(self):
        self.camera = None
        self.condition = threading.Condition()
        self.latest_jpeg = None       # encoded frame for all streaming clients
        self.brightest = {'x': 0, 'y': 0}
        self.is_running = False

    def start(self):
        """Start the camera and background capture loop."""
        if self.is_running:
            return

        try:
            self.camera = Picamera2()

            # Full sensor resolution for maximum FOV (~15fps)
            config = self.camera.create_video_configuration(
                main={"size": (1280, 720), "format": "BGR888"},
                # main={"size": (2592, 1944), "format": "RGB888"},
                controls={"FrameRate": 15}
            )
            self.camera.configure(config)
            self.camera.start()

            # Give camera time to warm up
            time.sleep(2)
            self.is_running = True
            print("Camera started successfully")

            # Single background thread owns the camera and feeds all clients
            thread = threading.Thread(target=self._capture_loop, daemon=True)
            thread.start()
        except Exception as e:
            print(f"Error starting camera: {e}")
            raise

    def stop(self):
        """Stop the camera."""
        self.is_running = False
        if self.camera:
            self.camera.stop()
            print("Camera stopped")

    def _capture_loop(self):
        """
        Background thread: captures frames, encodes them once, detects
        brightest pixel, then wakes all waiting stream clients.
        """
        while self.is_running:
            try:
                frame = self.camera.capture_array()

                # Encode to JPEG once for all clients
                buffer = io.BytesIO()
                Image.fromarray(frame).save(buffer, format='JPEG', quality=85)
                jpeg = buffer.getvalue()

                # Brightest pixel detection
                gray = np.mean(frame, axis=2)
                y, x = np.unravel_index(np.argmax(gray), gray.shape)

                # Publish to all waiting clients atomically
                with self.condition:
                    self.latest_jpeg = jpeg
                    self.brightest = {'x': int(x), 'y': int(y)}
                    self.condition.notify_all()

            except Exception as e:
                print(f"Capture error: {e}")

    def get_jpeg_frame(self):
        """
        Block until the next frame is ready, then return it.
        Each call to this from different threads returns the same frame
        simultaneously — no redundant camera reads.
        """
        with self.condition:
            self.condition.wait(timeout=5)
            return self.latest_jpeg

    def get_brightest_pixel(self):
        """Return the brightest pixel coordinates from the latest frame."""
        with self.condition:
            return self.brightest.copy()
