"""Konstanten + Konfigurations-Keys fuer die FanControl-IoT-Integration."""

from __future__ import annotations

DOMAIN = "fancontrol_iot"
MANUFACTURER = "Brogachy"
DEFAULT_NAME = "EUT-300B"

# ====================================================================
# Config-Entry-Keys (initiales Setup)
# ====================================================================
CONF_DEVICE_ID = "device_id"
CONF_LOCAL_KEY = "local_key"
CONF_ADDRESS = "address"
CONF_VERSION = "version"

DEFAULT_VERSION = 3.4

# ====================================================================
# Options-Keys (nachtraeglich editierbar in HA → Integration → Configure)
# ====================================================================

# --- Polling ---
CONF_SCAN_INTERVAL = "scan_interval"      # Sekunden
DEFAULT_SCAN_INTERVAL = 15

CONF_SOCKET_TIMEOUT = "socket_timeout"     # Sekunden
DEFAULT_SOCKET_TIMEOUT = 5

# --- DP-Mapping (Override fuer Geraete-Varianten) ---
CONF_DP_POWER = "dp_power"
CONF_DP_MODE = "dp_mode"
CONF_DP_SPEED = "dp_speed"
CONF_DP_TEMP_IN = "dp_temp_in"
CONF_DP_HUMID_IN = "dp_humid_in"
CONF_DP_TEMP_SET = "dp_temp_set"
CONF_DP_HUMID_SET = "dp_humid_set"
CONF_DP_TIMER = "dp_timer"

DEFAULT_DP_POWER = 1
DEFAULT_DP_MODE = 2
DEFAULT_DP_SPEED = 3
DEFAULT_DP_TEMP_IN = 18
DEFAULT_DP_HUMID_IN = 19
DEFAULT_DP_TEMP_SET = 22
DEFAULT_DP_HUMID_SET = 23
DEFAULT_DP_TIMER = 26

# Liste fuer Iteration in Options-Flow und Coordinator
DP_KEYS: tuple[tuple[str, int], ...] = (
    (CONF_DP_POWER, DEFAULT_DP_POWER),
    (CONF_DP_MODE, DEFAULT_DP_MODE),
    (CONF_DP_SPEED, DEFAULT_DP_SPEED),
    (CONF_DP_TEMP_IN, DEFAULT_DP_TEMP_IN),
    (CONF_DP_HUMID_IN, DEFAULT_DP_HUMID_IN),
    (CONF_DP_TEMP_SET, DEFAULT_DP_TEMP_SET),
    (CONF_DP_HUMID_SET, DEFAULT_DP_HUMID_SET),
    (CONF_DP_TIMER, DEFAULT_DP_TIMER),
)

# --- Speed-Range / Skalierung ---
CONF_SPEED_MIN = "speed_min"
CONF_SPEED_MAX = "speed_max"
DEFAULT_SPEED_MIN = 1
DEFAULT_SPEED_MAX = 10

# --- Temp-Skala (manche Geraete liefern *10, andere *1) ---
CONF_TEMP_SCALE = "temp_scale"
DEFAULT_TEMP_SCALE = 0.1   # d.h. 235 → 23.5°C

# --- Mode-Enum-Optionen (was die App schickt) ---
CONF_MODE_OPTIONS = "mode_options"
DEFAULT_MODE_OPTIONS = ["manual", "auto", "timer", "smart", "sleep"]

# --- Externe Sensoren / Verknuepfung (rein als Konfig fuer Cards/Automations) ---
CONF_OUTSIDE_TEMP_ENTITY = "outside_temp_entity"
CONF_WEATHER_ENTITY = "weather_entity"
CONF_NOTIFY_SERVICE = "notify_service"
DEFAULT_NOTIFY_SERVICE = "persistent_notification"

# --- Boost-Settings (fuer Card / Script) ---
CONF_BOOST_DURATION = "boost_duration"     # Minuten
CONF_BOOST_PERCENTAGE = "boost_percentage"  # 0..100
CONF_BOOST_AUTO_ENABLED = "boost_auto_enabled"
DEFAULT_BOOST_DURATION = 10
DEFAULT_BOOST_PERCENTAGE = 100
DEFAULT_BOOST_AUTO_ENABLED = False

# --- Plattformen ---
PLATFORMS = ["fan", "sensor", "number", "select"]

# --- UI-Defaults / Limits (nicht user-editierbar) ---
ROLE_LABELS = {
    "power":      "Power",
    "switch":     "Schalter",
    "mode":       "Modus",
    "speed":      "Drehzahl",
    "temp_in":    "Temperatur",
    "humid_in":   "Feuchte",
    "temp_set":   "Soll-Temperatur",
    "humid_set":  "Soll-Feuchte",
    "timer":      "Timer",
}

# Set-Ranges fuer Sollwerte (Number-Entities) — fix, weil Geraete-spezifisch
TEMP_MIN = 0.0
TEMP_MAX = 50.0
TEMP_STEP = 0.5

HUMID_MIN = 0
HUMID_MAX = 100
HUMID_STEP = 1

TIMER_MIN = 0
TIMER_MAX = 24 * 3600
TIMER_STEP = 60


def get_option(entry, key: str, default):
    """Helper: Options ueber Entry abrufen, Fallback auf Default."""
    return entry.options.get(key, entry.data.get(key, default))
