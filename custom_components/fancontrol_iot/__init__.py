"""FanControl-IoT — Home Assistant Integration fuer Brogachy / Smart-Farmers-Tuya-Luefter."""

from __future__ import annotations

import logging
from pathlib import Path

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

# ====================================================================
# Lovelace-Strategy: registriert ein JS-Modul, das automatisch die
# 3 Dashboard-Views (Lüfter / Schwellwerte / Einstellungen) generiert.
# ====================================================================
STRATEGY_VERSION = "0.5.2"
STRATEGY_URL = "/fancontrol_iot/fancontrol-strategy.js"
STRATEGY_FILE = Path(__file__).parent / "frontend" / "fancontrol-strategy.js"
_FRONTEND_KEY = "_strategy_registered"


async def _async_register_strategy(hass: HomeAssistant) -> None:
    """Stellt die Strategy als statisches JS-Modul bereit und sorgt dafür,
    dass es von HA beim Laden des Frontends mitgeladen wird."""
    domain_data = hass.data.setdefault(DOMAIN, {})
    if domain_data.get(_FRONTEND_KEY):
        return

    # JS-Datei als statischen Pfad ausliefern
    try:
        from homeassistant.components.http import StaticPathConfig
        await hass.http.async_register_static_paths([
            StaticPathConfig(STRATEGY_URL, str(STRATEGY_FILE), False)
        ])
    except ImportError:  # Fallback alt-HA
        hass.http.register_static_path(STRATEGY_URL, str(STRATEGY_FILE), False)

    # In Frontend als Extra-Modul mitladen — damit ist die Strategy
    # in allen Dashboards verfügbar, ohne dass der User Resources pflegen muss.
    try:
        from homeassistant.components.frontend import add_extra_js_url
        add_extra_js_url(hass, f"{STRATEGY_URL}?v={STRATEGY_VERSION}")
    except Exception:  # noqa: BLE001
        _LOGGER.warning("FanControl-Strategy konnte nicht als Extra-JS registriert werden.")

    domain_data[_FRONTEND_KEY] = True
    _LOGGER.info("FanControl-Strategy registriert (%s).", STRATEGY_URL)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Setup einer Geraete-Instanz aus dem Config-Entry."""
    await _async_register_strategy(hass)

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
