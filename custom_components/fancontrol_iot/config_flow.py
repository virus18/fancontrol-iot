"""UI-Setup-Flow fuer die FanControl-IoT-Integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_NAME
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_ADDRESS,
    CONF_DEVICE_ID,
    CONF_LOCAL_KEY,
    CONF_VERSION,
    DEFAULT_NAME,
    DEFAULT_VERSION,
    DOMAIN,
)
from .coordinator import TuyaClient

_LOGGER = logging.getLogger(__name__)

VERSION_OPTIONS = [3.3, 3.4, 3.5]


def _user_schema(defaults: dict | None = None) -> vol.Schema:
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
            # Eindeutig anhand device_id
            await self.async_set_unique_id(user_input[CONF_DEVICE_ID])
            self._abort_if_unique_id_configured()

            # Live-Test: tinytuya-Verbindung probieren
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
            data_schema=_user_schema(user_input),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(entry: ConfigEntry) -> OptionsFlow:
        return FanControlOptionsFlow(entry)


class FanControlOptionsFlow(OptionsFlow):
    """Spaeteres Editieren (z.B. IP-Adresse oder Version)."""

    def __init__(self, entry: ConfigEntry):
        self.entry = entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None) -> FlowResult:
        if user_input is not None:
            new_data = {**self.entry.data, **user_input}
            self.hass.config_entries.async_update_entry(self.entry, data=new_data)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(
            step_id="init",
            data_schema=_user_schema(self.entry.data),
        )
