"""Switch-Plattform — Trigger-Switches (invertiert) + Child Lock + Unit."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchDeviceClass, SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, TRIGGER_SWITCH_ROLES
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


# (role, translation_key, icon)
TRIGGER_DEFS = (
    ("sw_auto_high_temp",   "auto_high_temp",   "mdi:thermometer-chevron-up"),
    ("sw_auto_high_humid",  "auto_high_humid",  "mdi:water-percent-alert"),
    ("sw_auto_low_temp",    "auto_low_temp",    "mdi:thermometer-chevron-down"),
    ("sw_auto_low_humid",   "auto_low_humid",   "mdi:water-minus"),
    ("sw_alarm_high_temp",  "alarm_high_temp",  "mdi:thermometer-alert"),
    ("sw_alarm_high_humid", "alarm_high_humid", "mdi:water-alert"),
    ("sw_alarm_low_temp",   "alarm_low_temp",   "mdi:snowflake-alert"),
    ("sw_alarm_low_humid",  "alarm_low_humid",  "mdi:water-off"),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = []
    for role, tkey, icon in TRIGGER_DEFS:
        if coordinator.dp_for(role) > 0:
            entities.append(TriggerSwitch(coordinator, role, tkey, icon))
    if coordinator.dp_for("child_lock") > 0:
        entities.append(ChildLockSwitch(coordinator))
    if coordinator.dp_for("unit_display") > 0:
        entities.append(DisplayCelsiusSwitch(coordinator))
    async_add_entities(entities)


class _BaseSwitch(FanControlBaseEntity, SwitchEntity):
    """Gemeinsame Basis — die Rolle bestimmt das Verhalten."""
    _attr_device_class = SwitchDeviceClass.SWITCH


class TriggerSwitch(_BaseSwitch):
    """Trigger-Switch mit invertiertem Encoding ("0"=ON, "1"=OFF) — gekapselt."""

    def __init__(self, coordinator: FanControlCoordinator,
                 role: str, translation_key: str, icon: str):
        super().__init__(coordinator, f"sw_{role}")
        self._role = role
        self._attr_translation_key = translation_key
        self._attr_icon = icon

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.trigger_is_on(self._role)

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_trigger(self._role, True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_trigger(self._role, False)


class ChildLockSwitch(_BaseSwitch):
    """Child Lock (normales Encoding: "1" = lock)."""

    _attr_translation_key = "child_lock"
    _attr_icon = "mdi:lock"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "child_lock")

    @property
    def is_on(self) -> bool | None:
        v = self.coordinator.dp_value("child_lock")
        return None if v is None else str(v) == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_role("child_lock", "1")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_role("child_lock", "0")


class DisplayCelsiusSwitch(_BaseSwitch):
    """Display-Einheit: ON = °C, OFF = °F.

    Hat KEINEN Einfluss auf die Werte die das Gerät liefert (die kommen
    immer in °F). Steuert nur, was am Geräte-Display steht."""

    _attr_translation_key = "display_celsius"
    _attr_icon = "mdi:temperature-celsius"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "display_celsius")

    @property
    def is_on(self) -> bool | None:
        v = self.coordinator.dp_value("unit_display")
        return None if v is None else str(v) == "1"

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_role("unit_display", "1")

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_role("unit_display", "0")
