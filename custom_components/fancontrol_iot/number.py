"""Number-Plattform — Schwellwerte, Kalibrierungen, Brightness."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    HUMID_MAX,
    HUMID_MIN,
    HUMID_STEP,
    TEMP_THRESHOLD_ROLES,
    HUMID_THRESHOLD_ROLES,
)
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


def _f_to_c(f: float) -> float:
    return (f - 32.0) * 5.0 / 9.0


def _c_to_f(c: float) -> int:
    return int(round(c * 9.0 / 5.0 + 32.0))


# (role, translation_key)
TEMP_THRESHOLD_DEFS = (
    ("auto_high_temp",  "auto_high_temp"),
    ("auto_low_temp",   "auto_low_temp"),
    ("alarm_high_temp", "alarm_high_temp"),
    ("alarm_low_temp",  "alarm_low_temp"),
)
HUMID_THRESHOLD_DEFS = (
    ("auto_high_humid",  "auto_high_humid"),
    ("auto_low_humid",   "auto_low_humid"),
    ("alarm_high_humid", "alarm_high_humid"),
    ("alarm_low_humid",  "alarm_low_humid"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[NumberEntity] = []

    # Temperatur-Schwellwerte (°C, intern °F)
    for role, tkey in TEMP_THRESHOLD_DEFS:
        if coordinator.dp_for(role) > 0:
            entities.append(TempThresholdNumber(coordinator, role, tkey))

    # Feuchte-Schwellwerte (%)
    for role, tkey in HUMID_THRESHOLD_DEFS:
        if coordinator.dp_for(role) > 0:
            entities.append(HumidThresholdNumber(coordinator, role, tkey))

    # Kalibrierungen
    if coordinator.dp_for("temp_calibration") > 0:
        entities.append(TempCalibration(coordinator))
    if coordinator.dp_for("humid_calibration") > 0:
        entities.append(HumidCalibration(coordinator))

    # Display-Brightness
    if coordinator.dp_for("brightness") > 0:
        entities.append(BrightnessNumber(coordinator))

    # Direkter Drehzahl-Slider (Stufe 0-10) — redundant zur Fan-Entity,
    # aber praktisch für direkte Dashboard-Steuerung.
    if coordinator.dp_for("speed") > 0:
        entities.append(SpeedStageNumber(coordinator))

    async_add_entities(entities)


class _BaseNumber(FanControlBaseEntity, NumberEntity):
    pass


class TempThresholdNumber(_BaseNumber):
    """Temperatur-Schwellwert: HA-Anzeige in °C, intern wird °F geschrieben."""

    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = -10.0
    _attr_native_max_value = 60.0
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-lines"

    def __init__(self, coordinator: FanControlCoordinator, role: str, translation_key: str):
        super().__init__(coordinator, role)
        self._role = role
        self._attr_translation_key = translation_key

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value(self._role)
        if raw is None:
            return None
        try:
            return round(_f_to_c(float(raw)), 1)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_role(self._role, _c_to_f(value))


class HumidThresholdNumber(_BaseNumber):
    """Feuchte-Schwellwert in %."""

    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = HUMID_MIN
    _attr_native_max_value = HUMID_MAX
    _attr_native_step = HUMID_STEP
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:water-percent"

    def __init__(self, coordinator: FanControlCoordinator, role: str, translation_key: str):
        super().__init__(coordinator, role)
        self._role = role
        self._attr_translation_key = translation_key

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value(self._role)
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_role(self._role, int(round(value)))


class TempCalibration(_BaseNumber):
    """Temperatur-Kalibrierung (°F-Offset, ganzzahlig). Wird vom Gerät auf
    den Messwert addiert. Schritt 1°F ≈ 0.56°C."""

    _attr_native_unit_of_measurement = UnitOfTemperature.FAHRENHEIT
    _attr_native_min_value = -20
    _attr_native_max_value = 20
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:thermometer-plus"
    _attr_translation_key = "temp_calibration"
    _attr_entity_category = "config"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "temp_calibration")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value("temp_calibration")
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_role("temp_calibration", int(round(value)))


class HumidCalibration(_BaseNumber):
    """Feuchte-Kalibrierung (%-Offset)."""

    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = -20
    _attr_native_max_value = 20
    _attr_native_step = 1
    _attr_mode = NumberMode.BOX
    _attr_icon = "mdi:water-plus"
    _attr_translation_key = "humid_calibration"
    _attr_entity_category = "config"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "humid_calibration")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value("humid_calibration")
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_role("humid_calibration", int(round(value)))


class SpeedStageNumber(_BaseNumber):
    """Direkte Drehzahl als Stufe 0-10 (0 = Aus). Schreibt auf DP 102.
    Liest den Setpoint, nicht den Ist-Wert (sonst zappelt der Slider bei
    Notbetrieb)."""

    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:fan-speed-1"
    _attr_translation_key = "speed_stage"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "speed_stage")
        self._attr_native_min_value = float(coordinator.speed_min) if coordinator.speed_min == 0 else 0.0
        self._attr_native_max_value = float(coordinator.speed_max)

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value("speed")
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        v = int(round(value))
        lo, hi = 0, self.coordinator.speed_max
        v = max(lo, min(hi, v))
        await self.coordinator.async_set_role("speed", v)


class BrightnessNumber(_BaseNumber):
    """Display-Helligkeit (1–3)."""

    _attr_native_min_value = 1
    _attr_native_max_value = 3
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER
    _attr_icon = "mdi:brightness-6"
    _attr_translation_key = "brightness"
    _attr_entity_category = "config"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "brightness")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value("brightness")
        try:
            return float(raw) if raw is not None else None
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_role("brightness", int(round(value)))
