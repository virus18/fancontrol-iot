"""Polling-Koordinator + tinytuya-Wrapper fuer die HA-Integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import tinytuya
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


class TuyaClient:
    """Async-faehiger Wrapper um tinytuya.OutletDevice.

    tinytuya selber ist sync und nicht thread-safe — wir serialisieren alle
    Zugriffe mit einem asyncio.Lock und delegieren die blocking-IO mittels
    `run_in_executor` an HAs Executor-Pool.
    """

    def __init__(self, device_id: str, local_key: str, address: str, version: float):
        self.device_id = device_id
        self.local_key = local_key
        self.address = address
        self.version = float(version)
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
        dev.set_socketTimeout(5)
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
    """Pollt den Luefter und stellt die DPs den Entities zur Verfuegung."""

    def __init__(self, hass: HomeAssistant, client: TuyaClient, entry: ConfigEntry):
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{entry.entry_id[:8]}",
            update_interval=DEFAULT_SCAN_INTERVAL,
        )
        self.client = client
        self.entry = entry

    async def _async_update_data(self) -> dict[str, Any]:
        try:
            data = await self.client.async_status(self.hass)
        except Exception as e:
            raise UpdateFailed(f"tinytuya status failed: {e}") from e
        dps = data.get("dps") if isinstance(data.get("dps"), dict) else {}
        # Stringkeys nach int normalisieren ist unzuverlaessig — Entities greifen
        # ueber str(dp) zu. Wir geben die rohe Map weiter.
        return {str(k): v for k, v in dps.items()}

    def dp(self, key: int | str, default: Any = None) -> Any:
        return (self.data or {}).get(str(key), default)

    async def async_set_dp(self, dp: int, value: Any) -> None:
        await self.client.async_set_dp(self.hass, dp, value)
        # optimistisches Update + Refresh
        if self.data is not None:
            self.data[str(dp)] = value
            self.async_set_updated_data(self.data)
        await self.async_request_refresh()

    async def async_close(self) -> None:
        await self.client.async_close(self.hass)
