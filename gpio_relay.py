"""
gpio_relay.py - Relay abstraction for GPIO 18

The Joy-IT relay module is active LOW:
  - RELAY_ACTIVE_HIGH = False  → GPIO LOW  = relay ON  = pump running
  - RELAY_ACTIVE_HIGH = True   → GPIO HIGH = relay ON  = pump running

Change RELAY_ACTIVE_HIGH if you swap to a different relay module.
"""

from gpiozero import OutputDevice

# --- Configuration ---
RELAY_PIN = 18
RELAY_ACTIVE_HIGH = False   # Joy-IT relay is active LOW


class Relay:
    def __init__(self):
        self._device = OutputDevice(
            RELAY_PIN,
            active_high=RELAY_ACTIVE_HIGH,
            initial_value=False  # always start with pump OFF
        )

    def turn_on(self):
        self._device.on()

    def turn_off(self):
        self._device.off()

    def toggle(self):
        self._device.toggle()

    @property
    def is_on(self):
        return self._device.is_active

    def cleanup(self):
        self._device.close()
