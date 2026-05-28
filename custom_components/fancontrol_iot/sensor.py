"""Sensor-Plattform — gemessene Temperatur und Feuchte."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DP_HUMID_IN, DP_TEMP_IN
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TemperatureSensor(coordinator),
            HumiditySensor(coordinator),
        ]
    )


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
        raw = self.coordinator.dp(DP_TEMP_IN)
        if raw is None:
            return None
        try:
            return float(raw) / 10.0
        except (TypeError, ValueError):
            return None


class HumiditySensor(_BaseSensor):
    _attr_device_class = SensorDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_translation_key = "humidity"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "humidity")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp(DP_HUMID_IN)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None
