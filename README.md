# Gartenpi

Controls a Bosch 18V garden pump via a relay on GPIO 18, with a mobile-friendly web interface served by Flask and accessible over Tailscale.

## Hardware

- Raspberry Pi 2
- Joy-IT relay module (active LOW, diode included)
- Bosch GardenPump 18V-2000
- StromPi 3 (powered by the 18V battery, UART on GPIO 14/15)

## Requirements

- Raspberry Pi OS Trixie (headless)
- Tailscale installed and connected
- Python 3

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/gartenpi.git
cd gartenpi
```

### 2. Create a virtual environment and install dependencies

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
```

### 3. Enable the serial port for StromPi 3

```bash
sudo raspi-config
# Interface Options → Serial Port
# "Login shell over serial?" → No
# "Serial port hardware enabled?" → Yes
sudo reboot
```

### 4. Move the template into the templates folder

Flask requires templates to be in a `templates/` subfolder:

```bash
mkdir -p ~/gartenpi/templates
mv ~/gartenpi/index.html ~/gartenpi/templates/
```

### 5. Test the relay manually

```bash
python3 test_relay_low.py
```

Listen for a click. If the relay does not activate, try `test_relay_high.py` and update `RELAY_ACTIVE_HIGH` in `gpio_relay.py` accordingly.

### 6. Test the Flask app manually

```bash
python3 app.py
```

Open `http://<tailscale-ip>:5000` in your browser. Verify the button toggles the relay.

Press `Ctrl+C` to stop.

### 7. Install the systemd service

```bash
sudo cp gartenpi.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable gartenpi
sudo systemctl start gartenpi
```

Check it is running:

```bash
sudo systemctl status gartenpi
```

The app now starts automatically on every boot.

## Configuration

All configuration is at the top of `gpio_relay.py`:

| Variable | Default | Description |
|---|---|---|
| `RELAY_PIN` | `18` | BCM GPIO pin number |
| `RELAY_ACTIVE_HIGH` | `False` | Set to `True` for active HIGH relay modules |
| `MAX_RUNTIME_MINUTES` | `15` | Failsafe timeout — pump turns off automatically after this many minutes |

The timeout can also be changed at runtime via the web UI without restarting the service.

## Accessing the interface

Open `http://<tailscale-ip>:5000` from any device on your Tailscale network.

## Useful commands

```bash
# View live logs
sudo journalctl -u gartenpi -f

# Restart after a code change
sudo systemctl restart gartenpi

# Stop the service
sudo systemctl stop gartenpi
```