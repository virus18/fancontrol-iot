"""Binary-Sensor-Plattform — Hardware-Alarm-Indikator."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AlarmTriggeredSensor(coordinator)])


class AlarmTriggeredSensor(FanControlBaseEntity, BinarySensorEntity):
    """An sobald DP 105 == "8" — Hardware-Alarm aktiv (Lüfter im Notbetrieb)."""

    _attr_device_class = BinarySensorDeviceClass.PROBLEM
    _attr_translation_key = "alarm_triggered"
    _attr_icon = "mdi:alarm-light"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "alarm_triggered")

    @property
    def is_on(self) -> bool:
        return self.coordinator.is_alarm_active
