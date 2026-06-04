#!/usr/bin/env python3
"""
strompi.py - Command-line tool for managing the StromPi 3

Usage:
    sudo python3 strompi.py status
    sudo python3 strompi.py voltages
    sudo python3 strompi.py mode <1-6>
    sudo python3 strompi.py warnings on|off
    sudo python3 strompi.py monitor [--interval SECONDS]
    sudo python3 strompi.py raw "<command>"

Modes:
    1: mUSB  -> Wide
    2: Wide  -> mUSB
    3: mUSB  -> Battery
    4: Wide  -> Battery
    5: mUSB  -> Wide  -> Battery
    6: Wide  -> mUSB  -> Battery
"""

import argparse
import serial
import sys
import time
from datetime import datetime

# --- Configuration ---
SERIAL_PORT = "/dev/serial0"
BAUDRATE    = 38400
CHAR_DELAY  = 0.02   # delay between characters to prevent dropped chars
CMD_DELAY   = 0.4    # delay after sending a command

# ANSI colors for monitor output
RED    = "\033[91m"
GREEN  = "\033[92m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
RESET  = "\033[0m"


# ----------------------------------------------------------------------
# Serial helpers
# ----------------------------------------------------------------------

def open_serial():
    """Open the serial port to the StromPi."""
    try:
        return serial.Serial(
            SERIAL_PORT, BAUDRATE,
            timeout=0.5, bytesize=8, stopbits=1, parity=serial.PARITY_NONE
        )
    except serial.SerialException as e:
        sys.exit(f"Failed to open {SERIAL_PORT}: {e}")


def send(s, cmd):
    """Send a command character-by-character to avoid dropped bytes."""
    for ch in cmd:
        s.write(ch.encode())
        time.sleep(CHAR_DELAY)
    s.write(b"\r")
    time.sleep(CMD_DELAY)


def read_response(s, wait=1.0):
    """Read whatever the StromPi has sent."""
    time.sleep(wait)
    data = s.read(s.in_waiting or 1)
    return data.decode("utf-8", errors="replace")


def enter_console(s):
    """Enter the StromPi console mode."""
    send(s, "quit")           # ensure we're not already in some menu
    send(s, "startstrompiconsole")
    time.sleep(0.5)
    s.reset_input_buffer()


# ----------------------------------------------------------------------
# Commands
# ----------------------------------------------------------------------

def cmd_status(s):
    """Pretty-print show-status."""
    enter_console(s)
    send(s, "show-status")
    print(read_response(s, wait=1.5).strip())


def cmd_voltages(s):
    """Pretty-print adc-output."""
    enter_console(s)
    send(s, "adc-output")
    print(read_response(s, wait=1.0).strip())


def cmd_mode(s, mode):
    """Set the StromPi power-path mode (1-6) using serial commands + save."""
    if mode not in range(1, 7):
        sys.exit("Mode must be between 1 and 6")
    send(s, "quit")
    send(s, f"set-config 1 {mode}")
    send(s, "set-config 0 1")    # save + restart
    time.sleep(2)                # give StromPi time to restart
    print(f"Mode set to {mode}, StromPi restarted.")


def cmd_warnings(s, state):
    """Enable or disable powerfail warnings."""
    val = 1 if state == "on" else 0
    send(s, "quit")
    send(s, f"set-config 16 {val}")
    send(s, "set-config 0 0")    # save without restart
    time.sleep(1)
    print(f"Powerfail warnings: {'enabled' if val else 'disabled'}")


def cmd_raw(s, command):
    """Send a raw command and print the response."""
    enter_console(s)
    send(s, command)
    print(read_response(s, wait=1.5).strip())


# ----------------------------------------------------------------------
# Monitor mode
# ----------------------------------------------------------------------

def parse_voltage(line):
    """Extract voltage value (or 'not connected') from a status line."""
    if "not connected" in line.lower():
        return "  --   "
    try:
        return line.split(":", 1)[1].strip()
    except IndexError:
        return "?"


def get_snapshot(s):
    """Return a dict of current voltages and the powerfail counter."""
    snap = {"Wide": "?", "Bat": "?", "USB": "?", "Out": "?", "PFC": "?"}
    # adc-output for voltages
    send(s, "adc-output")
    data = read_response(s, wait=0.7)
    for line in data.splitlines():
        if "Wide-Range" in line:    snap["Wide"] = parse_voltage(line)
        elif "Battery"   in line:   snap["Bat"]  = parse_voltage(line)
        elif "microUSB"  in line:   snap["USB"]  = parse_voltage(line)
        elif "Output"    in line:   snap["Out"]  = parse_voltage(line)
    # show-status for powerfail counter
    send(s, "show-status")
    data = read_response(s, wait=1.0)
    for line in data.splitlines():
        if "Powerfailure-Counter" in line:
            try:
                snap["PFC"] = int(line.split(":")[1].strip())
            except (ValueError, IndexError):
                pass
    return snap


def cmd_monitor(s, interval):
    """Live monitor: voltages, powerfail counter delta, async events."""
    enter_console(s)
    print(f"{CYAN}StromPi monitor (Ctrl+C to quit){RESET}")
    print(f"{'time':10} {'Wide':>16} {'Bat':>16} {'USB':>16} {'Out':>16} {'PFC':>10} {'Δ':>6}")
    print("-" * 90)

    last_pfc = None
    try:
        while True:
            snap = get_snapshot(s)
            ts = datetime.now().strftime("%H:%M:%S")

            # compute delta
            delta_str = "-"
            if isinstance(snap["PFC"], int):
                if last_pfc is not None:
                    delta = snap["PFC"] - last_pfc
                    if delta > 0:
                        delta_str = f"{RED}+{delta}{RESET}"
                    else:
                        delta_str = f"{GREEN}{delta:+d}{RESET}"
                last_pfc = snap["PFC"]

            print(f"{ts:10} "
                  f"{snap['Wide']:>16} "
                  f"{snap['Bat']:>16} "
                  f"{snap['USB']:>16} "
                  f"{snap['Out']:>16} "
                  f"{str(snap['PFC']):>10} "
                  f"{delta_str:>15}")
            time.sleep(interval)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}stopped{RESET}")


# ----------------------------------------------------------------------
# Main / argument parsing
# ----------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Manage and monitor the StromPi 3.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("status",   help="show current StromPi configuration")
    sub.add_parser("voltages", help="show current voltage readings")

    p_mode = sub.add_parser("mode", help="set power-path mode (1-6)")
    p_mode.add_argument("value", type=int, choices=range(1, 7))

    p_warn = sub.add_parser("warnings", help="enable/disable powerfail warnings")
    p_warn.add_argument("state", choices=["on", "off"])

    p_mon = sub.add_parser("monitor", help="live monitor of voltages + powerfail events")
    p_mon.add_argument("--interval", type=float, default=2.0,
                       help="seconds between samples (default: 2)")

    p_raw = sub.add_parser("raw", help="send a raw command to the StromPi")
    p_raw.add_argument("command", help="command string to send")

    args = parser.parse_args()
    s = open_serial()

    try:
        if   args.command == "status":   cmd_status(s)
        elif args.command == "voltages": cmd_voltages(s)
        elif args.command == "mode":     cmd_mode(s, args.value)
        elif args.command == "warnings": cmd_warnings(s, args.state)
        elif args.command == "monitor":  cmd_monitor(s, args.interval)
        elif args.command == "raw":      cmd_raw(s, args.command)
    finally:
        s.close()


if __name__ == "__main__":
    main()