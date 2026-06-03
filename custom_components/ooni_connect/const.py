"""Constants for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ooni_connect"

# How often the coordinator runs as a connection watchdog. Fresh measurements
# arrive asynchronously via BLE notifications, so this interval mainly drives
# reconnect attempts when the device is out of range.
UPDATE_INTERVAL = timedelta(seconds=60)

# Timeout (seconds) for establishing a single BLE connection attempt.
# Home Assistant recommends at least 10s for BLE connects.
CONNECT_TIMEOUT = 20

# How many background connection attempts to make per watchdog cycle.
CONNECT_RETRIES = 3

# Seconds to wait between failed connection attempts.
RETRY_BACKOFF = 2

MANUFACTURER = "Ooni"
MODEL = "Digital Thermometer"
DEFAULT_NAME = "Ooni Hub"
