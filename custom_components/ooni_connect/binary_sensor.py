"""Binary sensor platform for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import OoniConnectCoordinator

# Key of the special sensor that reports the Bluetooth link itself.
CONNECTION_KEY = "status_connected"

BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key=CONNECTION_KEY,
        translation_key="status_connected",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="probe_p1_connected",
        translation_key="probe_p1_connected",
        device_class=BinarySensorDeviceClass.PLUG,
    ),
    BinarySensorEntityDescription(
        key="probe_p2_connected",
        translation_key="probe_p2_connected",
        device_class=BinarySensorDeviceClass.PLUG,
    ),
    # Eco mode is a plain on/off state; no device_class maps cleanly to it.
    BinarySensorEntityDescription(
        key="eco_mode",
        translation_key="eco_mode",
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Ooni binary sensors."""
    coordinator: OoniConnectCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OoniBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )


class OoniBinarySensor(
    CoordinatorEntity[OoniConnectCoordinator], BinarySensorEntity
):
    """Represents an Ooni on/off state."""

    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: OoniConnectCoordinator,
        description: BinarySensorEntityDescription,
    ) -> None:
        """Initialize the binary sensor."""
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
    def is_on(self) -> bool | None:
        """Return the current state."""
        # The connectivity sensor reflects the real BLE link state.
        if self.entity_description.key == CONNECTION_KEY:
            return self.coordinator.connected

        data = self.coordinator.data
        if data is None:
            return None
        return bool(getattr(data, self.entity_description.key, False))

    @property
    def available(self) -> bool:
        """Determine availability."""
        # The connectivity sensor must always be available so it can report
        # "off" when the device is out of range.
        if self.entity_description.key == CONNECTION_KEY:
            return True
        return self.coordinator.connected and self.coordinator.data is not None
