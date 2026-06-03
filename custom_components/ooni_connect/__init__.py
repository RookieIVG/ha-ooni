"""The Ooni Connect Bluetooth integration."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, CONF_NAME, Platform
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import OoniConnectCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Ooni Connect from a config entry."""
    coordinator = OoniConnectCoordinator(
        hass,
        entry.data[CONF_ADDRESS],
        entry.data[CONF_NAME],
    )

    # Returns immediately with no data; the connection is established in the
    # background and measurements arrive via BLE notifications.
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry and release the BLE connection."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator: OoniConnectCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        # Important: the Ooni hub only accepts a single BLE connection. Without
        # this, a stale connection would block reconnection after a reload.
        await coordinator.async_shutdown()
    return unload_ok
