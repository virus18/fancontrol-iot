"""Select-Plattform — Modus. Optionen kommen aus Coordinator.mode_options."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
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
    async_add_entities([ModeSelect(coordinator)])


class ModeSelect(FanControlBaseEntity, SelectEntity):
    _attr_translation_key = "mode"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "mode")

    @property
    def options(self) -> list[str]:
        return self.coordinator.mode_options

    @property
    def current_option(self) -> str | None:
        val = self.coordinator.dp_value("mode")
        return None if val is None else str(val)

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.async_set_role("mode", option)
