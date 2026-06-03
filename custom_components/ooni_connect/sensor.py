"""Sensor platform for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import OoniConnectCoordinator

_LOGGER = logging.getLogger(__name__)

# Probe temperature keys map to the flag telling us whether the probe is
# physically plugged in. When it isn't, the raw value is meaningless, so we
# report None (unavailable) instead of a stray reading.
PROBE_CONNECTED_FLAG: dict[str, str] = {
    "probe_p1": "probe_p1_connected",
    "probe_p2": "probe_p2_connected",
}

SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="battery",
        translation_key="battery",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="ambient_a",
        translation_key="ambient_a",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="ambient_b",
        translation_key="ambient_b",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="probe_p1",
        translation_key="probe_p1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="probe_p2",
        translation_key="probe_p2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ooni sensors."""
    coordinator: OoniConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OoniTemperatureSensor(coordinator, description)
        for description in SENSOR_TYPES
    )


class OoniTemperatureSensor(
    CoordinatorEntity[OoniConnectCoordinator], SensorEntity
):
    """Represents a single Ooni measurement sensor."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OoniConnectCoordinator,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.address)},
            connections={(CONNECTION_BLUETOOTH, coordinator.address)},
            name=coordinator.device_name,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    @property
    def native_value(self) -> Any:
        """Return the current value, or None if unavailable/not connected."""
        data = self.coordinator.data
        if data is None:
            return None

        # Suppress probe temperatures when the probe isn't plugged in.
        flag = PROBE_CONNECTED_FLAG.get(self.entity_description.key)
        if flag is not None and not getattr(data, flag, False):
            return None

        return getattr(data, self.entity_description.key, None)

    @property
    def available(self) -> bool:
        """A sensor is available only while connected and holding data."""
        return self.coordinator.connected and self.coordinator.data is not None
