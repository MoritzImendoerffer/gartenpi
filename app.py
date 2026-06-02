"""
app.py - Gartenpi pump control web interface

Endpoints:
  GET  /            - web UI
  POST /toggle      - toggle pump on/off
  GET  /status      - returns pump state, remaining seconds, timeout as JSON
  POST /timeout     - update the failsafe timeout (body: {"minutes": N})

Run manually:    python3 app.py
Run as service:  see gartenpi.service
"""

from flask import Flask, render_template, jsonify, request
from gpio_relay import Relay
import atexit

app = Flask(__name__)
relay = Relay()


@app.route("/")
def index():
    return render_template("index.html",
        is_on=relay.is_on,
        timeout_minutes=relay.timeout_minutes
    )


@app.route("/toggle", methods=["POST"])
def toggle():
    relay.toggle()
    return jsonify({
        "is_on": relay.is_on,
        "remaining_seconds": relay.remaining_seconds,
        "timeout_minutes": relay.timeout_minutes
    })


@app.route("/status")
def status():
    return jsonify({
        "is_on": relay.is_on,
        "remaining_seconds": relay.remaining_seconds,
        "timeout_minutes": relay.timeout_minutes
    })


@app.route("/timeout", methods=["POST"])
def set_timeout():
    data = request.get_json()
    minutes = data.get("minutes")
    if not minutes or not str(minutes).isdigit() or int(minutes) < 1:
        return jsonify({"error": "Invalid timeout value"}), 400
    relay.set_timeout(int(minutes))
    return jsonify({"timeout_minutes": relay.timeout_minutes})


# Clean up GPIO on shutdown
@atexit.register
def cleanup():
    relay.cleanup()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)