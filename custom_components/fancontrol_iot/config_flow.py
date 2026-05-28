"""Konfig + Options-Flow mit Multi-Step-Menue.

Initiales Setup: nur Connection (device_id, key, IP, version).
Spaeter ueber "Configure"-Button im Geraete-Eintrag erreichbar:
 - Connection
 - Polling
 - DP-Mapping (Advanced)
 - Speed-Range
 - Externe Sensoren / Notifications
 - Boost-Defaults
"""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_ADDRESS,
    CONF_BOOST_AUTO_ENABLED,
    CONF_BOOST_DURATION,
    CONF_BOOST_PERCENTAGE,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_MODE_OPTIONS,
    CONF_NOTIFY_SERVICE,
    CONF_OUTSIDE_TEMP_ENTITY,
    CONF_SCAN_INTERVAL,
    CONF_SOCKET_TIMEOUT,
    CONF_SPEED_MAX,
    CONF_SPEED_MIN,
    CONF_TEMP_SCALE,
    CONF_VERSION,
    CONF_WEATHER_ENTITY,
    DEFAULT_BOOST_AUTO_ENABLED,
    DEFAULT_BOOST_DURATION,
    DEFAULT_BOOST_PERCENTAGE,
    DEFAULT_MODE_OPTIONS,
    DEFAULT_NAME,
    DEFAULT_NOTIFY_SERVICE,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOCKET_TIMEOUT,
    DEFAULT_SPEED_MAX,
    DEFAULT_SPEED_MIN,
    DEFAULT_TEMP_SCALE,
    DEFAULT_VERSION,
    DOMAIN,
    DP_KEYS,
    get_option,
)
from .coordinator import TuyaClient

_LOGGER = logging.getLogger(__name__)

VERSION_OPTIONS = [3.3, 3.4, 3.5]


# ====================================================================
# Initial Setup (ConfigFlow)
# ====================================================================

def _connection_schema(defaults: dict | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_NAME, default=d.get(CONF_NAME, DEFAULT_NAME)): str,
            vol.Required(CONF_DEVICE_ID, default=d.get(CONF_DEVICE_ID, "")): str,
            vol.Required(CONF_LOCAL_KEY, default=d.get(CONF_LOCAL_KEY, "")): str,
            vol.Required(CONF_ADDRESS, default=d.get(CONF_ADDRESS, "")): str,
            vol.Required(CONF_VERSION, default=d.get(CONF_VERSION, DEFAULT_VERSION)):
                vol.In(VERSION_OPTIONS),
        }
    )


class FanControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Erstmaliges Einrichten via UI."""

    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            client = TuyaClient(
                device_id=user_input[CONF_DEVICE_ID],
                local_key=user_input[CONF_LOCAL_KEY],
                address=user_input[CONF_ADDRESS],
                version=float(user_input[CONF_VERSION]),
            )
            try:
                data = await client.async_status(self.hass)
            except Exception as e:
                _LOGGER.warning("Connect-Test fehlgeschlagen: %s", e)
                errors["base"] = "cannot_connect"
            else:
                dps = data.get("dps") if isinstance(data.get("dps"), dict) else {}
                if not dps:
                    errors["base"] = "no_data"
                else:
                    await client.async_close(self.hass)
                    return self.async_create_entry(
                        title=user_input[CONF_NAME],
                        data=user_input,
                    )
            await client.async_close(self.hass)

        return self.async_show_form(
            step_id="user",
            data_schema=_connection_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return FanControlOptionsFlow(entry)


# ====================================================================
# Options-Flow mit Menue
# ====================================================================

class FanControlOptionsFlow(OptionsFlow):
    """Multi-step options:
        - connection (Endpoints: ID/Key/IP/Version)
        - polling    (Scan-Interval, Socket-Timeout)
        - dp_mapping (DP-Overrides)
        - speed      (Min/Max + Temp-Skalierung)
        - external   (Outside-Temp, Wetter-Entity, Notify-Service)
        - boost      (Dauer, Drehzahl, Auto-Boost)
    """

    def __init__(self, entry: ConfigEntry):
        self.entry = entry
        self._pending: dict[str, Any] = {}  # Buffer fuer Multi-Step

    # ---- Menue ----

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        return self.async_show_menu(
            step_id="init",
            menu_options=[
                "connection",
                "polling",
                "dp_mapping",
                "speed",
                "external",
                "boost",
            ],
        )

    # ---- Connection ----

    async def async_step_connection(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            new_data = {**self.entry.data, **user_input}
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            return self.async_create_entry(title="", data=self.entry.options)

        return self.async_show_form(
            step_id="connection",
            data_schema=_connection_schema(self.entry.data),
        )

    # ---- Polling ----

    async def async_step_polling(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self._save_options(user_input)

        cur = self.entry.options
        return self.async_show_form(
            step_id="polling",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SCAN_INTERVAL,
                        default=cur.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
                    ): vol.All(int, vol.Range(min=3, max=600)),
                    vol.Required(
                        CONF_SOCKET_TIMEOUT,
                        default=cur.get(CONF_SOCKET_TIMEOUT, DEFAULT_SOCKET_TIMEOUT),
                    ): vol.All(int, vol.Range(min=1, max=30)),
                }
            ),
        )

    # ---- DP-Mapping (Advanced) ----

    async def async_step_dp_mapping(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self._save_options(user_input)

        cur = self.entry.options
        schema = {
            vol.Required(key, default=cur.get(key, default)):
                vol.All(int, vol.Range(min=1, max=255))
            for key, default in DP_KEYS
        }
        return self.async_show_form(
            step_id="dp_mapping",
            data_schema=vol.Schema(schema),
            description_placeholders={
                "note": "Nur aendern wenn dein Geraet abweichende DP-Nummern hat."
            },
        )

    # ---- Speed-Range ----

    async def async_step_speed(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self._save_options(user_input)

        cur = self.entry.options
        return self.async_show_form(
            step_id="speed",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SPEED_MIN,
                        default=cur.get(CONF_SPEED_MIN, DEFAULT_SPEED_MIN),
                    ): vol.All(int, vol.Range(min=0, max=100)),
                    vol.Required(
                        CONF_SPEED_MAX,
                        default=cur.get(CONF_SPEED_MAX, DEFAULT_SPEED_MAX),
                    ): vol.All(int, vol.Range(min=1, max=100)),
                    vol.Required(
                        CONF_TEMP_SCALE,
                        default=cur.get(CONF_TEMP_SCALE, DEFAULT_TEMP_SCALE),
                    ): vol.In({0.1: "x0.1 (z.B. 235 → 23.5°C)", 1.0: "x1 (direkt °C)"}),
                    vol.Required(
                        CONF_MODE_OPTIONS,
                        default=", ".join(
                            cur.get(CONF_MODE_OPTIONS, DEFAULT_MODE_OPTIONS)
                        ),
                    ): str,
                }
            ),
        )

    # ---- External: outside temp / weather / notify ----

    async def async_step_external(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self._save_options(user_input)

        cur = self.entry.options
        return self.async_show_form(
            step_id="external",
            data_schema=vol.Schema(
                {
                    vol.Optional(
                        CONF_OUTSIDE_TEMP_ENTITY,
                        default=cur.get(CONF_OUTSIDE_TEMP_ENTITY, ""),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="sensor", device_class="temperature")
                    ),
                    vol.Optional(
                        CONF_WEATHER_ENTITY,
                        default=cur.get(CONF_WEATHER_ENTITY, ""),
                    ): selector.EntitySelector(
                        selector.EntitySelectorConfig(domain="weather")
                    ),
                    vol.Optional(
                        CONF_NOTIFY_SERVICE,
                        default=cur.get(CONF_NOTIFY_SERVICE, DEFAULT_NOTIFY_SERVICE),
                    ): str,
                }
            ),
        )

    # ---- Boost-Defaults ----

    async def async_step_boost(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            return self._save_options(user_input)

        cur = self.entry.options
        return self.async_show_form(
            step_id="boost",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_BOOST_DURATION,
                        default=cur.get(CONF_BOOST_DURATION, DEFAULT_BOOST_DURATION),
                    ): vol.All(int, vol.Range(min=1, max=240)),
                    vol.Required(
                        CONF_BOOST_PERCENTAGE,
                        default=cur.get(CONF_BOOST_PERCENTAGE, DEFAULT_BOOST_PERCENTAGE),
                    ): vol.All(int, vol.Range(min=10, max=100)),
                    vol.Required(
                        CONF_BOOST_AUTO_ENABLED,
                        default=cur.get(CONF_BOOST_AUTO_ENABLED, DEFAULT_BOOST_AUTO_ENABLED),
                    ): bool,
                }
            ),
        )

    # ---- Persistenz-Helper ----

    def _save_options(self, new_options: dict[str, Any]) -> FlowResult:
        # MODE_OPTIONS: String → Liste konvertieren
        if CONF_MODE_OPTIONS in new_options and isinstance(new_options[CONF_MODE_OPTIONS], str):
            new_options[CONF_MODE_OPTIONS] = [
                o.strip() for o in new_options[CONF_MODE_OPTIONS].split(",") if o.strip()
            ]
        merged = {**self.entry.options, **new_options}
        return self.async_create_entry(title="", data=merged)
