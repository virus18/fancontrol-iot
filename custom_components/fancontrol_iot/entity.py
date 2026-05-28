"""Basis-Entity fuer FanControl-IoT (DeviceInfo + CoordinatorEntity)."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER
from .coordinator import FanControlCoordinator


class FanControlBaseEntity(CoordinatorEntity[FanControlCoordinator]):
    """Liefert konsistente device_info ueber alle Plattformen hinweg."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: FanControlCoordinator, key: str):
        super().__init__(coordinator)
        device_id = coordinator.entry.data["device_id"]
        self._attr_unique_id = f"{device_id}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, device_id)},
            name=coordinator.entry.title,
            manufacturer=MANUFACTURER,
            model="EUT-Reihe (Tuya-EC-Fan)",
            configuration_url=f"http://{coordinator.entry.data['address']}",
        )
