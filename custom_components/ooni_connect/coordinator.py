"""DataUpdateCoordinator for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONNECT_RETRIES,
    CONNECT_TIMEOUT,
    DOMAIN,
    RETRY_BACKOFF,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class OoniConnectCoordinator(DataUpdateCoordinator[Any]):
    """Manage the BLE connection to the Ooni Digital Thermometer.

    The device pushes measurements over BLE notifications. We therefore treat
    the coordinator's polling interval as a reconnect watchdog rather than an
    active poll: ``_async_update_data`` never blocks, it only ensures a
    connection attempt is running and returns the last known data. Fresh values
    arrive through ``_handle_bluetooth_update``.
    """

    def __init__(self, hass: HomeAssistant, address: str, name: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=UPDATE_INTERVAL,
        )
        self.address = address
        self.device_name = name
        self.client: Any = None
        self._lock = asyncio.Lock()
        self._connection_task: asyncio.Task[None] | None = None

    @property
    def connected(self) -> bool:
        """Return True while an active BLE connection is held."""
        return self.client is not None and self.client.is_connected

    @callback
    def _handle_bluetooth_update(self, data: Any) -> None:
        """Handle a notification packet coming from the device.

        The underlying BLE backend may invoke this from a thread other than the
        event loop, so we hop back onto the loop to stay thread-safe.
        """
        self.hass.loop.call_soon_threadsafe(self.async_set_updated_data, data)

    def _on_disconnected(self, *args: Any) -> None:
        """Handle an unexpected disconnect.

        Clearing the data lets all entities flip to "unavailable" instead of
        showing the last (now stale) measurement, and notifies the connectivity
        sensor that the link is gone.
        """
        _LOGGER.warning("Ooni connection lost")
        self.client = None
        self.hass.loop.call_soon_threadsafe(self.async_set_updated_data, None)

    async def _async_update_data(self) -> Any:
        """Watchdog: ensure a connection attempt runs, return last known data."""
        if not self.connected and (
            self._connection_task is None or self._connection_task.done()
        ):
            self._connection_task = self.hass.async_create_task(
                self._connect_in_background()
            )
        return self.data

    async def _connect_in_background(self) -> None:
        """(Re)establish the BLE connection without blocking Home Assistant."""
        # Imported lazily so the (heavier) BLE backend isn't loaded until we
        # actually connect. The library is vendored inside this integration.
        from .ooni_connect_bluetooth.client import Client

        async with self._lock:
            if self.connected:
                return

            ble_device = async_ble_device_from_address(
                self.hass, self.address, connectable=True
            )
            if ble_device is None:
                _LOGGER.debug("Ooni device %s not in range", self.address)
                return

            for attempt in range(1, CONNECT_RETRIES + 1):
                try:
                    async with asyncio.timeout(CONNECT_TIMEOUT):
                        self.client = await Client.connect(
                            device=ble_device,
                            notify_callback=self._handle_bluetooth_update,
                            disconnected_callback=self._on_disconnected,
                        )
                    _LOGGER.debug("Connected to Ooni device %s", self.address)
                    return
                except asyncio.CancelledError:
                    raise
                except Exception as err:  # noqa: BLE001 - backend raises broadly
                    self.client = None
                    _LOGGER.debug(
                        "Ooni connection attempt %s/%s failed: %s",
                        attempt,
                        CONNECT_RETRIES,
                        err,
                    )
                    if attempt < CONNECT_RETRIES:
                        await asyncio.sleep(RETRY_BACKOFF)

    async def async_shutdown(self) -> None:
        """Cancel the reconnect task and close the BLE connection on unload."""
        await super().async_shutdown()

        if self._connection_task is not None and not self._connection_task.done():
            self._connection_task.cancel()

        client = self.client
        self.client = None
        if client is not None:
            try:
                await client.disconnect()
            except Exception as err:  # noqa: BLE001
                _LOGGER.debug("Error while disconnecting from Ooni: %s", err)
