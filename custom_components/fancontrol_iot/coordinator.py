"""Polling-Koordinator + tinytuya-Wrapper.

Liest Polling-Intervall, Socket-Timeout und DP-Mapping aus den Options
des Config-Entries — bei Aenderung wird die Integration automatisch neu
geladen (Hook in __init__.py).
"""

from __future__ import annotations

import asyncio
import logging
from datetime import timedelta
from typing import Any

import tinytuya
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    ALARM_FLAG_VALUE,
    DEFAULT_MODE_OPTIONS,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_SOCKET_TIMEOUT,
    DEFAULT_SPEED_MAX,
    DEFAULT_SPEED_MIN,
    DEFAULT_TEMP_SCALE,
    DEFAULT_TEMP_UNIT_INPUT,
    DOMAIN,
    CONF_MODE_OPTIONS,
    CONF_SCAN_INTERVAL,
    CONF_SOCKET_TIMEOUT,
    CONF_SPEED_MAX,
    CONF_SPEED_MIN,
    CONF_TEMP_SCALE,
    CONF_TEMP_UNIT_INPUT,
    DP_KEYS,
    EXTRA_DP_ROLES,
    TEMP_UNIT_FAHRENHEIT,
    TRIGGER_SWITCH_ROLES,
)

_LOGGER = logging.getLogger(__name__)


class TuyaClient:
    """Async-faehiger Wrapper um tinytuya.OutletDevice.

    tinytuya selber ist sync und nicht thread-safe — wir serialisieren alle
    Zugriffe mit einem asyncio.Lock und delegieren die blocking-IO mittels
    `run_in_executor` an HAs Executor-Pool.
    """

    def __init__(
        self,
        device_id: str,
        local_key: str,
        address: str,
        version: float,
        socket_timeout: int = DEFAULT_SOCKET_TIMEOUT,
    ):
        self.device_id = device_id
        self.local_key = local_key
        self.address = address
        self.version = float(version)
        self.socket_timeout = int(socket_timeout)
        self._device: tinytuya.OutletDevice | None = None
        self._lock = asyncio.Lock()

    def _connect_sync(self) -> tinytuya.OutletDevice:
        dev = tinytuya.OutletDevice(
            dev_id=self.device_id,
            address=self.address,
            local_key=self.local_key,
        )
        dev.set_version(self.version)
        dev.set_socketPersistent(True)
        dev.set_socketTimeout(self.socket_timeout)
        return dev

    async def _ensure(self, hass: HomeAssistant) -> tinytuya.OutletDevice:
        if self._device is None:
            self._device = await hass.async_add_executor_job(self._connect_sync)
        return self._device

    async def async_close(self, hass: HomeAssistant) -> None:
        if self._device is not None:
            try:
                await hass.async_add_executor_job(self._device.close)
            except Exception:
                pass
            self._device = None

    async def async_status(self, hass: HomeAssistant) -> dict[str, Any]:
        async with self._lock:
            dev = await self._ensure(hass)
            try:
                data = await hass.async_add_executor_job(dev.status)
            except Exception as e:
                _LOGGER.warning("status exception: %s — reconnect", e)
                await self.async_close(hass)
                dev = await self._ensure(hass)
                data = await hass.async_add_executor_job(dev.status)

            if isinstance(data, dict) and ("Error" in data or "Err" in data):
                _LOGGER.warning("status error: %s — reconnect", data.get("Error") or data.get("Err"))
                await self.async_close(hass)
                dev = await self._ensure(hass)
                data = await hass.async_add_executor_job(dev.status)
            return data if isinstance(data, dict) else {"raw": data}

    async def async_set_dp(self, hass: HomeAssistant, dp: int, value: Any) -> dict[str, Any]:
        async with self._lock:
            dev = await self._ensure(hass)
            res = await hass.async_add_executor_job(dev.set_value, int(dp), value)
            return res if isinstance(res, dict) else {"raw": res}


class FanControlCoordinator(DataUpdateCoordinator[dict[str, Any]]):
    """Pollt den Luefter und haelt das DP-Mapping aus den Options vor.

    Entities greifen ueber `dp_for("power")` usw. zu — so liegt das
    Mapping zentral und ist user-konfigurierbar.
    """

    def __init__(self, hass: HomeAssistant, client: TuyaClient, entry: ConfigEntry):
        scan_interval = entry.options.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id[:8]}",
            update_interval=timedelta(seconds=int(scan_interval)),
        )
        self.client = client
        self.entry = entry
        self._dp_map = self._build_dp_map(entry)

    # ---- Options-derived caches ----

    @staticmethod
    def _build_dp_map(entry: ConfigEntry) -> dict[str, int]:
        """role -> dp-nummer Mapping aus Options + Defaults.

        Klassische DP_KEYS (per Options einstellbar) + erweiterte Rollen
        (fest defaultet, da Gerät-modell-spezifisch — User kann später per
        Options-Flow erweitern)."""
        out: dict[str, int] = {}
        for conf_key, default in DP_KEYS:
            role = conf_key.replace("dp_", "")
            out[role] = int(entry.options.get(conf_key, default))
        for role, default in EXTRA_DP_ROLES:
            # Override-Möglichkeit via Options ("dp_<role>"-Key)
            out[role] = int(entry.options.get(f"dp_{role}", default))
        return out

    def dp_for(self, role: str) -> int:
        """Liefert die konfigurierte DP-Nummer fuer eine Rolle (power/speed/...)."""
        return self._dp_map.get(role, 0)

    @property
    def speed_min(self) -> int:
        return int(self.entry.options.get(CONF_SPEED_MIN, DEFAULT_SPEED_MIN))

    @property
    def speed_max(self) -> int:
        return int(self.entry.options.get(CONF_SPEED_MAX, DEFAULT_SPEED_MAX))

    @property
    def temp_scale(self) -> float:
        return float(self.entry.options.get(CONF_TEMP_SCALE, DEFAULT_TEMP_SCALE))

    @property
    def temp_unit_input(self) -> str:
        """Liefert 'fahrenheit' oder 'celsius'. Bei 'fahrenheit' rechnet
        der Temp-Sensor automatisch in °C um (EUT-300B liefert °F)."""
        return str(self.entry.options.get(CONF_TEMP_UNIT_INPUT, DEFAULT_TEMP_UNIT_INPUT))

    @property
    def temp_input_is_fahrenheit(self) -> bool:
        return self.temp_unit_input == TEMP_UNIT_FAHRENHEIT

    # ---- Alarm / Notbetrieb-Auswertung ----

    @property
    def is_alarm_active(self) -> bool:
        """Hardware-Alarm aktiv (Gerät boosted Lüfter auf Max)."""
        return str(self.dp_value("alarm_flag", "0")) == ALARM_FLAG_VALUE

    def actual_speed(self) -> int | None:
        """Tatsächlich laufende Drehzahl — nicht der Setpoint, sondern was
        das Gerät real ausführt (kann durch Alarm-Boost vom Setpoint abweichen).
        Bevorzugt DP 103, fällt auf DP 102 zurück wenn nicht verfügbar."""
        v = self.dp_value("speed_actual")
        if v is None:
            v = self.dp_value("speed")
        try:
            return int(v) if v is not None else None
        except (TypeError, ValueError):
            return None

    # ---- Trigger-Switch-Konvertierung (INVERTIERT) ----

    @staticmethod
    def is_trigger_switch(role: str) -> bool:
        return role in TRIGGER_SWITCH_ROLES

    def trigger_is_on(self, role: str) -> bool | None:
        """Trigger-Switches haben invertiertes Encoding: '0' = ON, '1' = OFF.
        Liefert sauberen Bool für HA-Entities."""
        v = self.dp_value(role)
        if v is None:
            return None
        return str(v) == "0"

    async def async_set_trigger(self, role: str, on: bool) -> None:
        """Schreibt einen Trigger-Switch invertiert (HA-ON -> '0', HA-OFF -> '1')."""
        await self.async_set_role(role, "0" if on else "1")

    @property
    def power_and_speed_share_dp(self) -> bool:
        """Wenn power-DP == speed-DP (wie beim EUT-300B mit DP 102), nutzen
        wir Speed-as-Power-Semantik: 0 = Aus, >0 = An mit Drehzahl."""
        return self.dp_for("power") == self.dp_for("speed") > 0

    @property
    def mode_options(self) -> list[str]:
        opts = self.entry.options.get(CONF_MODE_OPTIONS, DEFAULT_MODE_OPTIONS)
        if isinstance(opts, str):
            return [o.strip() for o in opts.split(",") if o.strip()]
        return list(opts)

    # ---- Polling ----

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_status(self.hass)
        except Exception as e:
            raise UpdateFailed(f"tinytuya status failed: {e}") from e
        dps = data.get("dps") if isinstance(data.get("dps"), dict) else {}
        return {str(k): v for k, v in dps.items()}

    def dp_value(self, role: str, default: Any = None) -> Any:
        """Holt den Wert eines DP nach Rolle (z.B. dp_value("power"))."""
        return (self.data or {}).get(str(self.dp_for(role)), default)

    async def async_set_role(self, role: str, value: Any) -> None:
        """Setzt einen DP per Rollen-Namen."""
        dp = self.dp_for(role)
        if dp <= 0:
            _LOGGER.warning("Role %s ohne DP-Nummer — uebersprungen", role)
            return
        await self.client.async_set_dp(self.hass, dp, value)
        if self.data is not None:
            self.data[str(dp)] = value
            self.async_set_updated_data(self.data)
        await self.async_request_refresh()

    async def async_close(self) -> None:
        await self.client.async_close(self.hass)
