"""Sensor-Plattform — Temperatur + Feuchte. Temp-Skala kommt aus Options."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import ALARM_FLAG_VALUE, DOMAIN
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SensorEntity] = [
        TemperatureSensor(coordinator),
        HumiditySensor(coordinator),
    ]
    if coordinator.dp_for("alarm_flag") > 0:
        entities.append(CountdownSensor(coordinator))
    async_add_entities(entities)


class _BaseSensor(FanControlBaseEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT


class TemperatureSensor(_BaseSensor):
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_translation_key = "temperature"
    _attr_suggested_display_precision = 1

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "temperature")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value("temp_in")
        if raw is None:
            return None
        try:
            scaled = float(raw) * self.coordinator.temp_scale
        except (TypeError, ValueError):
            return None
        # EUT-300B liefert °F-Integer (z.B. 71). Umrechnen auf °C wenn so konfiguriert.
        if self.coordinator.temp_input_is_fahrenheit:
            return round((scaled - 32.0) * 5.0 / 9.0, 1)
        return scaled


class HumiditySensor(_BaseSensor):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_translation_key = "humidity"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "humidity")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp_value("humid_in")
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None


class CountdownSensor(FanControlBaseEntity, SensorEntity):
    """Timer-Countdown in Sekunden. DP 105 ist überladen — der Wert "8"
    bedeutet 'Alarm aktiv' (siehe AlarmTriggeredSensor) und wird hier als 0
    behandelt, damit der Countdown-Sensor nicht fälschlich 8s anzeigt."""

    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_icon = "mdi:timer-sand"
    _attr_translation_key = "countdown"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "countdown")

    @property
    def native_value(self) -> int | None:
        raw = self.coordinator.dp_value("alarm_flag")
        if raw is None:
            return None
        s = str(raw)
        if s == ALARM_FLAG_VALUE:        # "8" = Alarm — separater binary_sensor
            return 0
        try:
            return max(0, int(s))
        except (TypeError, ValueError):
            return None
