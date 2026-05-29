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

# Defaults sind auf den Brogachy EUT-300B (Smart-Farmers-Variante, xfj) kalibriert:
#   DP 102 ist der Master-DP (0 = Aus, 1-10 = Drehzahl). Power und Speed teilen
#   sich denselben DP → fan.py erkennt das und nutzt 0/>0 als On/Off-Semantik.
#   Temperatur (DP 9) kommt als °F-Integer; sensor.py rechnet via
#   temp_unit_input nach °C um. Setpoints (Soll-Temp/Humid) hat dieses Modell
#   nicht direkt — stattdessen 8 Schwellwerte (Auto + Alarm × Hi/Lo × T/H).
DEFAULT_DP_POWER = 102
DEFAULT_DP_MODE = 2
DEFAULT_DP_SPEED = 102
DEFAULT_DP_SPEED_ACTUAL = 103   # gemessener Wert inkl. Notbetrieb (DP 102 = Setpoint)
DEFAULT_DP_TEMP_IN = 9
DEFAULT_DP_HUMID_IN = 8
DEFAULT_DP_TEMP_SET = 0
DEFAULT_DP_HUMID_SET = 0
DEFAULT_DP_TIMER = 0            # dieses Modell hat keinen schreibbaren Timer
DEFAULT_DP_BRIGHTNESS = 101
DEFAULT_DP_ALARM_FLAG = 105     # "0" = idle, "8" = Alarm aktiv (Gerät boosted Luefter)

# Schwellwerte (alle °F bzw. % im Geraet)
DEFAULT_DP_AUTO_HIGH_TEMP  = 106
DEFAULT_DP_AUTO_HIGH_HUMID = 107
DEFAULT_DP_AUTO_LOW_TEMP   = 108
DEFAULT_DP_AUTO_LOW_HUMID  = 109
DEFAULT_DP_ALARM_HIGH_TEMP  = 110
DEFAULT_DP_ALARM_HIGH_HUMID = 111
DEFAULT_DP_ALARM_LOW_TEMP   = 112
DEFAULT_DP_ALARM_LOW_HUMID  = 113

# Setting-Switches (normales Encoding 0/1)
DEFAULT_DP_CHILD_LOCK   = 114   # 0 = unlock, 1 = lock
DEFAULT_DP_UNIT_DISPLAY = 115   # 1 = °C, 0 = °F (nur App-Anzeige)

# Trigger-Switches (INVERTIERTES Encoding: "0" = ON, "1" = OFF)
DEFAULT_DP_SW_AUTO_HIGH_TEMP   = 116
DEFAULT_DP_SW_AUTO_HIGH_HUMID  = 117
DEFAULT_DP_SW_AUTO_LOW_TEMP    = 118
DEFAULT_DP_SW_AUTO_LOW_HUMID   = 119
DEFAULT_DP_SW_ALARM_HIGH_TEMP  = 120
DEFAULT_DP_SW_ALARM_HIGH_HUMID = 121
DEFAULT_DP_SW_ALARM_LOW_TEMP   = 122
DEFAULT_DP_SW_ALARM_LOW_HUMID  = 123

# Kalibrierungen (°F-Offset bzw. %-Offset, signed int)
DEFAULT_DP_TEMP_CALIBRATION  = 124
DEFAULT_DP_HUMID_CALIBRATION = 125

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
DEFAULT_TEMP_SCALE = 1.0   # EUT-300B liefert ganze Zahl (z.B. 71 fuer 71°F)

# --- Temperatur-Eingangs-Einheit (Geraet liefert °F oder °C ueber DP) ---
CONF_TEMP_UNIT_INPUT = "temp_unit_input"
TEMP_UNIT_FAHRENHEIT = "fahrenheit"
TEMP_UNIT_CELSIUS = "celsius"
DEFAULT_TEMP_UNIT_INPUT = TEMP_UNIT_FAHRENHEIT   # EUT-300B: °F intern -> HA rechnet nach °C

# --- Mode-Enum-Optionen (was die App schickt) ---
CONF_MODE_OPTIONS = "mode_options"
DEFAULT_MODE_OPTIONS = ["ON", "TIMER", "AUTO", "ALARM"]

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
PLATFORMS = ["fan", "sensor", "binary_sensor", "number", "select", "switch"]

# ====================================================================
# Erweitertes Rollen-Mapping (für EUT-300B-Vollausstattung).
# Coordinator.dp_for() liest hier nach. Reihenfolge: (role, default-DP).
# ====================================================================
EXTRA_DP_ROLES: tuple[tuple[str, int], ...] = (
    ("speed_actual",    DEFAULT_DP_SPEED_ACTUAL),
    ("brightness",      DEFAULT_DP_BRIGHTNESS),
    ("alarm_flag",      DEFAULT_DP_ALARM_FLAG),

    ("auto_high_temp",  DEFAULT_DP_AUTO_HIGH_TEMP),
    ("auto_high_humid", DEFAULT_DP_AUTO_HIGH_HUMID),
    ("auto_low_temp",   DEFAULT_DP_AUTO_LOW_TEMP),
    ("auto_low_humid",  DEFAULT_DP_AUTO_LOW_HUMID),
    ("alarm_high_temp", DEFAULT_DP_ALARM_HIGH_TEMP),
    ("alarm_high_humid",DEFAULT_DP_ALARM_HIGH_HUMID),
    ("alarm_low_temp",  DEFAULT_DP_ALARM_LOW_TEMP),
    ("alarm_low_humid", DEFAULT_DP_ALARM_LOW_HUMID),

    ("child_lock",      DEFAULT_DP_CHILD_LOCK),
    ("unit_display",    DEFAULT_DP_UNIT_DISPLAY),

    ("sw_auto_high_temp",   DEFAULT_DP_SW_AUTO_HIGH_TEMP),
    ("sw_auto_high_humid",  DEFAULT_DP_SW_AUTO_HIGH_HUMID),
    ("sw_auto_low_temp",    DEFAULT_DP_SW_AUTO_LOW_TEMP),
    ("sw_auto_low_humid",   DEFAULT_DP_SW_AUTO_LOW_HUMID),
    ("sw_alarm_high_temp",  DEFAULT_DP_SW_ALARM_HIGH_TEMP),
    ("sw_alarm_high_humid", DEFAULT_DP_SW_ALARM_HIGH_HUMID),
    ("sw_alarm_low_temp",   DEFAULT_DP_SW_ALARM_LOW_TEMP),
    ("sw_alarm_low_humid",  DEFAULT_DP_SW_ALARM_LOW_HUMID),

    ("temp_calibration",  DEFAULT_DP_TEMP_CALIBRATION),
    ("humid_calibration", DEFAULT_DP_HUMID_CALIBRATION),
)

# Wertsemantik:
#   - Trigger-Switches (sw_*) sind INVERTIERT: "0" = ON, "1" = OFF.
#   - Setting-Switches (child_lock, unit_display) sind NORMAL: "1" = ON.
#   - Schwellwert-Temperaturen kommen in °F. Schwellwert-Feuchten in %.
#   - Kalibrierungen in °F-Offset / %-Offset.
TRIGGER_SWITCH_ROLES: tuple[str, ...] = (
    "sw_auto_high_temp", "sw_auto_high_humid", "sw_auto_low_temp", "sw_auto_low_humid",
    "sw_alarm_high_temp","sw_alarm_high_humid","sw_alarm_low_temp","sw_alarm_low_humid",
)
TEMP_THRESHOLD_ROLES: tuple[str, ...] = (
    "auto_high_temp", "auto_low_temp", "alarm_high_temp", "alarm_low_temp",
)
HUMID_THRESHOLD_ROLES: tuple[str, ...] = (
    "auto_high_humid", "auto_low_humid", "alarm_high_humid", "alarm_low_humid",
)
ALARM_FLAG_VALUE = "8"   # DP 105 == "8" => Alarm aktiv

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
