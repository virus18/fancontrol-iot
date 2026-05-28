"""Fan-Plattform — Power + Drehzahl."""

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

from .const import DOMAIN, DP_POWER, DP_SPEED, SPEED_MAX, SPEED_MIN
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity

SPEED_RANGE = (SPEED_MIN, SPEED_MAX)


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
        self._attr_name = None  # nutzt Device-Name als Entity-Name

    @property
    def is_on(self) -> bool | None:
        return bool(self.coordinator.dp(DP_POWER))

    @property
    def percentage(self) -> int | None:
        val = self.coordinator.dp(DP_SPEED)
        if val is None:
            return None
        try:
            return ranged_value_to_percentage(SPEED_RANGE, int(val))
        except (ValueError, TypeError):
            return None

    @property
    def speed_count(self) -> int:
        return SPEED_MAX - SPEED_MIN + 1

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        await self.coordinator.async_set_dp(DP_POWER, True)
        if percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_dp(DP_POWER, False)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            await self.coordinator.async_set_dp(DP_POWER, False)
            return
        value = int(percentage_to_ranged_value(SPEED_RANGE, percentage))
        value = max(SPEED_MIN, min(SPEED_MAX, value))
        # Bei Speed-Set Power gleich mit an, damit's nicht stumm bleibt
        if not self.is_on:
            await self.coordinator.async_set_dp(DP_POWER, True)
        await self.coordinator.async_set_dp(DP_SPEED, value)
