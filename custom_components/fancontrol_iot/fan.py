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
        # Bei EUT-300B: actual_speed (DP 103) ist die Quelle der Wahrheit —
        # das deckt auch den Notbetrieb ab (DP 103 = 10 bei Alarm, obwohl
        # DP 102 = 0). Bei Geräten ohne speed_actual: Fallback auf power-DP.
        if self.coordinator.power_and_speed_share_dp:
            actual = self.coordinator.actual_speed()
            if actual is None:
                return None
            return actual > 0
        return bool(self.coordinator.dp_value("power"))

    @property
    def percentage(self) -> int | None:
        # Anzeige folgt dem effektiv laufenden Wert (inkl. Auto-Boost bei Alarm).
        if self.coordinator.power_and_speed_share_dp:
            ival = self.coordinator.actual_speed()
        else:
            val = self.coordinator.dp_value("speed")
            try:
                ival = int(val) if val is not None else None
            except (ValueError, TypeError):
                ival = None
        if ival is None:
            return None
        if ival <= 0:
            return 0
        return ranged_value_to_percentage(self._speed_range, ival)

    @property
    def extra_state_attributes(self) -> dict:
        """Erweiterte Attribute, sichtbar in Developer-Tools/Templates."""
        c = self.coordinator
        attrs: dict = {}
        setpoint = c.dp_value("speed")
        actual   = c.actual_speed()
        if setpoint is not None: attrs["setpoint_stage"] = setpoint
        if actual is not None:   attrs["actual_stage"]   = actual
        attrs["alarm_active"] = c.is_alarm_active
        return attrs

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
        if self.coordinator.power_and_speed_share_dp:
            # Speed-as-Power: bei An ohne explizite Drehzahl -> Mitte des Bereichs
            if percentage is not None:
                await self.async_set_percentage(percentage)
                return
            lo, hi = self._speed_range
            await self.coordinator.async_set_role("speed", max(lo, hi // 2 or lo))
            return
        await self.coordinator.async_set_role("power", True)
        if percentage is not None:
            await self.async_set_percentage(percentage)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.coordinator.power_and_speed_share_dp:
            await self.coordinator.async_set_role("speed", 0)
            return
        await self.coordinator.async_set_role("power", False)

    async def async_set_percentage(self, percentage: int) -> None:
        if percentage <= 0:
            if self.coordinator.power_and_speed_share_dp:
                await self.coordinator.async_set_role("speed", 0)
            else:
                await self.coordinator.async_set_role("power", False)
            return
        lo, hi = self._speed_range
        value = int(percentage_to_ranged_value(self._speed_range, percentage))
        value = max(lo, min(hi, value))
        # Bei separater Power-DP: erst einschalten, dann Drehzahl
        if not self.coordinator.power_and_speed_share_dp and not self.is_on:
            await self.coordinator.async_set_role("power", True)
        await self.coordinator.async_set_role("speed", value)
