#!/usr/bin/env python3
"""
Servo control module using pigpiod
Controls SM-S4303R continuous rotation servos on GPIO17 and GPIO27
"""
import pigpio


class ServoController:
    """Manages servo motor control via pigpiod."""

    # GPIO pins for servos
    SERVO1_PIN = 17
    SERVO2_PIN = 27

    # Pulse width constants (microseconds)
    # SM-S4303R: 1500us = rest, <1500 = CW, >1500 = CCW
    MIN_PULSE = 500
    MAX_PULSE = 2500
    REST_PULSE = 1500

    def __init__(self):
        """Initialize connection to pigpiod daemon."""
        try:
            self.pi = pigpio.pi()
            if not self.pi.connected:
                raise Exception("Failed to connect to pigpiod daemon")

            # Initialize servos to rest position
            self.pi.set_servo_pulsewidth(self.SERVO1_PIN, 0)
            self.pi.set_servo_pulsewidth(self.SERVO2_PIN, 0)

            print("Servo controller initialized successfully")
        except Exception as e:
            print(f"Error initializing servo controller: {e}")
            print("Make sure pigpiod is running: sudo pigpiod")
            raise

    def set_servo(self, gpio_pin, pulse_width):
        """
        Set servo pulse width.

        Args:
            gpio_pin (int): GPIO pin number (17 or 27)
            pulse_width (int): Pulse width in microseconds (500-2500)
                              1500 = rest/stop
                              <1500 = clockwise (decreasing = faster)
                              >1500 = counter-clockwise (increasing = faster)
        """
        if gpio_pin not in [self.SERVO1_PIN, self.SERVO2_PIN]:
            raise ValueError(f"Invalid GPIO pin: {gpio_pin}")

        if not (self.MIN_PULSE <= pulse_width <= self.MAX_PULSE):
            raise ValueError(f"Pulse width must be between {self.MIN_PULSE} and {self.MAX_PULSE}")

        self.pi.set_servo_pulsewidth(gpio_pin, pulse_width)
        print(f"Set GPIO{gpio_pin} to {pulse_width}us")

    def stop_servo(self, gpio_pin):
        """
        Stop a servo by setting it to rest position.

        Args:
            gpio_pin (int): GPIO pin number (17 or 27)
        """
        if gpio_pin not in [self.SERVO1_PIN, self.SERVO2_PIN]:
            raise ValueError(f"Invalid GPIO pin: {gpio_pin}")

        self.pi.set_servo_pulsewidth(gpio_pin, self.REST_PULSE)
        print(f"Stopped GPIO{gpio_pin}")

    def cleanup(self):
        """Clean up GPIO and close connection to pigpiod."""
        try:
            # Stop both servos
            self.pi.set_servo_pulsewidth(self.SERVO1_PIN, 0)
            self.pi.set_servo_pulsewidth(self.SERVO2_PIN, 0)

            # Close connection
            self.pi.stop()
            print("Servo controller cleaned up")
        except Exception as e:
            print(f"Error during cleanup: {e}")
