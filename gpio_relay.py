"""
gpio_relay.py - Relay abstraction for GPIO 18

The Joy-IT relay module is active LOW:
  - RELAY_ACTIVE_HIGH = False  → GPIO LOW  = relay ON  = pump running
  - RELAY_ACTIVE_HIGH = True   → GPIO HIGH = relay ON  = pump running

Change RELAY_ACTIVE_HIGH if you swap to a different relay module.
Change MAX_RUNTIME_MINUTES to set the failsafe timeout.
"""

import threading
from gpiozero import OutputDevice

# --- Configuration ---
RELAY_PIN         = 18
RELAY_ACTIVE_HIGH = False  # Joy-IT relay is active LOW
MAX_RUNTIME_MINUTES = 15   # failsafe: pump turns off automatically after this


class Relay:
    def __init__(self):
        self._device = OutputDevice(
            RELAY_PIN,
            active_high=RELAY_ACTIVE_HIGH,
            initial_value=False  # always start with pump OFF
        )
        self._timer = None
        self._start_time = None
        self.max_runtime = MAX_RUNTIME_MINUTES * 60  # stored in seconds

    def turn_on(self):
        self._cancel_timer()
        self._device.on()
        self._start_time = threading.Event()  # used as a timestamp anchor
        self._start_time = __import__("time").time()
        self._timer = threading.Timer(self.max_runtime, self._timeout)
        self._timer.daemon = True
        self._timer.start()

    def turn_off(self):
        self._cancel_timer()
        self._device.off()

    def toggle(self):
        if self.is_on:
            self.turn_off()
        else:
            self.turn_on()

    def set_timeout(self, minutes):
        """Update the failsafe timeout in minutes. Takes effect on next turn_on."""
        self.max_runtime = max(1, int(minutes)) * 60

    @property
    def is_on(self):
        return self._device.is_active

    @property
    def remaining_seconds(self):
        """Seconds remaining before automatic shutoff. None if pump is off."""
        if not self.is_on or self._start_time is None:
            return None
        import time
        elapsed = time.time() - self._start_time
        remaining = self.max_runtime - elapsed
        return max(0, int(remaining))

    @property
    def timeout_minutes(self):
        """Current configured timeout in minutes."""
        return self.max_runtime // 60

    def _timeout(self):
        """Called automatically by the timer when max runtime is reached."""
        self._device.off()
        self._timer = None
        self._start_time = None

    def _cancel_timer(self):
        if self._timer:
            self._timer.cancel()
            self._timer = None
        self._start_time = None

    def cleanup(self):
        self._cancel_timer()
        self._device.close()