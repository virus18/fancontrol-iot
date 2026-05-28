"""Select-Plattform — Betriebsmodus."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, DP_MODE, MODE_OPTIONS
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ModeSelect(coordinator)])


class ModeSelect(FanControlBaseEntity, SelectEntity):
    _attr_options = MODE_OPTIONS
    _attr_translation_key = "mode"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "mode")

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.dp(DP_MODE)
        if val is None:
            return None
        s = str(val)
        # Wenn das Geraet einen Modus liefert, der nicht in MODE_OPTIONS ist,
        # geben wir ihn trotzdem zurueck — HA zeigt ihn als unbekannten Wert.
        return s

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_dp(DP_MODE, option)
