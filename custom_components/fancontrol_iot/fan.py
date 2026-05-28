"""Fan-Plattform — Power + Drehzahl. Liest DP-Nummern + Range aus Coordinator."""

from __future__ import annotations

from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from .const import DOMAIN
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([FanControlFan(coordinator)])


class FanControlFan(FanControlBaseEntity, FanEntity):
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
    )
    _attr_translation_key = "fan"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "fan")
        self._attr_name = None

    @property
    def _speed_range(self) -> tuple[int, int]:
        return (self.coordinator.speed_min, self.coordinator.speed_max)

    @property
    def is_on(self) -> bool | None:
        return bool(self.coordinator.dp_value("power"))

    @property
    def percentage(self) -> int | None:
        val = self.coordinator.dp_value("speed")
        if val is None:
            return None
        try:
            return ranged_value_to_percentage(self._speed_range, int(val))
        except (ValueError, TypeError):
            return None

    @property
    def speed_count(self) -> int:
        lo, hi = self._speed_range
        return max(1, hi - lo + 1)

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self.coordinator.async_set_role("power", True)
        if percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_role("power", False)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.coordinator.async_set_role("power", False)
            return
        lo, hi = self._speed_range
        value = int(percentage_to_ranged_value(self._speed_range, percentage))
        value = max(lo, min(hi, value))
        if not self.is_on:
            await self.coordinator.async_set_role("power", True)
        await self.coordinator.async_set_role("speed", value)
