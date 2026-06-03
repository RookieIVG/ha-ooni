"""Constants for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "ooni_connect"

# How often the coordinator runs as a connection watchdog. Fresh measurements
# arrive asynchronously via BLE notifications, so this interval mainly drives
# reconnect attempts when the device is out of range.
UPDATE_INTERVAL = timedelta(seconds=60)

# Minimum seconds to wait after a failed connection attempt before retrying,
# so we don't hammer the adapter/proxy every watchdog cycle.
MIN_RETRY_INTERVAL = 60

# Longer backoff when an ESPHome Bluetooth proxy runs out of connection slots;
# slots stay reserved for ~30-60s after a dropped attempt, so wait much longer.
OUT_OF_SLOTS_RETRY_INTERVAL = 300

# Attempts handed to bleak-retry-connector per connection try. Kept low so a
# single run doesn't exhaust all of a proxy's connection slots.
CONNECT_MAX_ATTEMPTS = 3

MANUFACTURER = "Ooni"
MODEL = "Digital Thermometer"
DEFAULT_NAME = "Ooni Hub"
