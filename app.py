"""
app.py - Gartenpi pump control web interface

Endpoints:
  GET  /           - web UI
  POST /toggle     - toggle pump on/off
  GET  /status     - returns pump state as JSON

Run manually:    python3 app.py
Run as service:  see gartenpi.service
"""

from flask import Flask, render_template, jsonify
from gpio_relay import Relay
import atexit

app = Flask(__name__)
relay = Relay()


@app.route("/")
def index():
    return render_template("index.html", is_on=relay.is_on)


@app.route("/toggle", methods=["POST"])
def toggle():
    relay.toggle()
    return jsonify({"is_on": relay.is_on})


@app.route("/status")
def status():
    return jsonify({"is_on": relay.is_on})


# Clean up GPIO on shutdown
@atexit.register
def cleanup():
    relay.cleanup()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
