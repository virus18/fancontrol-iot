"""Number-Plattform — Soll-Temperatur, Soll-Feuchte, Timer."""

from __future__ import annotations

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberMode,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature, UnitOfTime
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    DOMAIN,
    DP_HUMID_SET,
    DP_TEMP_SET,
    DP_TIMER,
    HUMID_MAX,
    HUMID_MIN,
    HUMID_STEP,
    TEMP_MAX,
    TEMP_MIN,
    TEMP_STEP,
    TIMER_MAX,
    TIMER_MIN,
    TIMER_STEP,
)
from .coordinator import FanControlCoordinator
from .entity import FanControlBaseEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: FanControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            TargetTemperature(coordinator),
            TargetHumidity(coordinator),
            TimerNumber(coordinator),
        ]
    )


class TargetTemperature(FanControlBaseEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = TEMP_MIN
    _attr_native_max_value = TEMP_MAX
    _attr_native_step = TEMP_STEP
    _attr_mode = NumberMode.SLIDER
    _attr_translation_key = "target_temperature"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "target_temperature")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp(DP_TEMP_SET)
        if raw is None:
            return None
        try:
            return float(raw) / 10.0
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_dp(DP_TEMP_SET, int(round(value * 10)))


class TargetHumidity(FanControlBaseEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.HUMIDITY
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_native_min_value = HUMID_MIN
    _attr_native_max_value = HUMID_MAX
    _attr_native_step = HUMID_STEP
    _attr_mode = NumberMode.SLIDER
    _attr_translation_key = "target_humidity"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "target_humidity")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp(DP_HUMID_SET)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_dp(DP_HUMID_SET, int(round(value)))


class TimerNumber(FanControlBaseEntity, NumberEntity):
    _attr_native_unit_of_measurement = UnitOfTime.SECONDS
    _attr_native_min_value = TIMER_MIN
    _attr_native_max_value = TIMER_MAX
    _attr_native_step = TIMER_STEP
    _attr_mode = NumberMode.BOX
    _attr_translation_key = "timer"

    def __init__(self, coordinator: FanControlCoordinator):
        super().__init__(coordinator, "timer")

    @property
    def native_value(self) -> float | None:
        raw = self.coordinator.dp(DP_TIMER)
        if raw is None:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.async_set_dp(DP_TIMER, int(round(value)))
