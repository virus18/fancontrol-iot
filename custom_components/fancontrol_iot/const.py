"""Konstanten fuer die FanControl-IoT-Integration."""

from __future__ import annotations

from datetime import timedelta

DOMAIN = "fancontrol_iot"
MANUFACTURER = "Brogachy"
DEFAULT_NAME = "EUT-300B"

# Config-Entry-Keys
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_ADDRESS = "address"
CONF_VERSION = "version"

DEFAULT_VERSION = 3.4
DEFAULT_SCAN_INTERVAL = timedelta(seconds=15)

# Plattformen, die diese Integration registriert
PLATFORMS = ["fan", "sensor", "number", "select"]

# DP-Mapping fuer Brogachy EUT-Reihe (siehe presets/brogachy_eut.json).
# Smart Farmers App ist eine Tuya-Whitelabel-App, deshalb gelten die ueblichen
# Tuya-Klima/Fan-Konventionen.
DP_POWER = 1            # bool
DP_MODE = 2             # str enum
DP_SPEED = 3            # int 1-10
DP_TEMP_IN = 18         # int (scale 0.1, °C)
DP_HUMID_IN = 19        # int (0..100, %)
DP_TEMP_SET = 22        # int (scale 0.1, °C)
DP_HUMID_SET = 23       # int (0..100, %)
DP_TIMER = 26           # int seconds

# Modus-Optionen wie sie typischerweise im "mode"-DP vorkommen.
# Wenn die App andere Strings sendet, wird die Option in der Select-Entity
# trotzdem angezeigt — HA filtert nicht hart.
MODE_OPTIONS = ["manual", "auto", "timer", "smart", "sleep"]

# Speed-Range — falls dein Geraet 1-9 oder 1-100 hat, beim Config-Flow ggf.
# anpassen. 1..10 ist Standard fuer EC-Inline-Fans.
SPEED_MIN = 1
SPEED_MAX = 10

# Set-Range fuer Temperatur (Werte sind im DP *10 dargestellt).
TEMP_MIN = 0.0
TEMP_MAX = 50.0
TEMP_STEP = 0.5

HUMID_MIN = 0
HUMID_MAX = 100
HUMID_STEP = 1

TIMER_MIN = 0
TIMER_MAX = 24 * 3600
TIMER_STEP = 60
