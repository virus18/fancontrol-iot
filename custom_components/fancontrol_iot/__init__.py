"""FanControl-IoT — Home Assistant Integration fuer Brogachy / Smart-Farmers-Tuya-Luefter."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_SOCKET_TIMEOUT,
    DEFAULT_SOCKET_TIMEOUT,
    DOMAIN,
    PLATFORMS,
)
from .coordinator import FanControlCoordinator, TuyaClient

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup einer Geraete-Instanz aus dem Config-Entry."""
    client = TuyaClient(
        device_id=entry.data["device_id"],
        local_key=entry.data["local_key"],
        address=entry.data["address"],
        version=float(entry.data.get("version", 3.4)),
        socket_timeout=int(entry.options.get(CONF_SOCKET_TIMEOUT, DEFAULT_SOCKET_TIMEOUT)),
    )

    coordinator = FanControlCoordinator(hass, client, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_options_updated))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Cleanup beim Entfernen / Reload."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: FanControlCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_close()
    return unload_ok


async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Bei Options-Aenderung: Integration neu laden, damit Scan-Interval,
    DP-Mapping etc. greifen."""
    await hass.config_entries.async_reload(entry.entry_id)
