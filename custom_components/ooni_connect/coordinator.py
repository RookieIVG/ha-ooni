"""DataUpdateCoordinator for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from bleak_retry_connector import BleakOutOfConnectionSlotsError
from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    CONNECT_MAX_ATTEMPTS,
    DOMAIN,
    MIN_RETRY_INTERVAL,
    OUT_OF_SLOTS_RETRY_INTERVAL,
    UPDATE_INTERVAL,
)

_LOGGER = logging.getLogger(__name__)


class OoniConnectCoordinator(DataUpdateCoordinator[Any]):
    """Manage the BLE connection to the Ooni Digital Thermometer.

    The device pushes measurements over BLE notifications, so the polling
    interval acts as a reconnect watchdog rather than an active poll:
    ``_async_update_data`` never blocks, it just makes sure a connection
    attempt is running (subject to a cooldown) and returns the last data.
    Fresh values arrive through ``_handle_bluetooth_update``.
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
        self._connecting = False
        self._last_connect_attempt: float = 0.0

    @property
    def connected(self) -> bool:
        """Return True while an active BLE connection is held."""
        return self.client is not None and self.client.is_connected

    @callback
    def _handle_bluetooth_update(self, data: Any) -> None:
        """Handle a notification packet coming from the device.

        The BLE backend may invoke this off the event loop thread, so we hop
        back onto the loop to stay thread-safe.
        """
        self.hass.loop.call_soon_threadsafe(self.async_set_updated_data, data)

    def _on_disconnected(self, *args: Any) -> None:
        """Handle an unexpected disconnect.

        Dropping the data lets every entity become unavailable instead of
        showing the last (now stale) reading, and refreshes the connectivity
        sensor immediately.
        """
        _LOGGER.warning("Ooni connection lost")
        self.client = None
        self.hass.loop.call_soon_threadsafe(self.async_set_updated_data, None)

    async def _async_update_data(self) -> Any:
        """Watchdog: ensure a connection attempt runs, respecting the cooldown."""
        if not self.connected:
            now = time.monotonic()
            if (
                not self._connecting
                and (now - self._last_connect_attempt) >= MIN_RETRY_INTERVAL
            ):
                # Set the flag AND timestamp BEFORE creating the task: the flag
                # blocks a second spawn before this one starts, the timestamp
                # blocks an immediate respawn if the task fails very quickly.
                self._connecting = True
                self._last_connect_attempt = now
                self._connection_task = self.hass.async_create_task(
                    self._connect_in_background()
                )
        return self.data

    async def _connect_in_background(self) -> None:
        """(Re)establish the BLE connection without blocking Home Assistant."""
        # Imported lazily so the BLE backend isn't loaded until we connect.
        # The library is vendored inside this integration.
        from .ooni_connect_bluetooth.client import Client

        try:
            async with self._lock:
                if self.connected:
                    return

                ble_device = async_ble_device_from_address(
                    self.hass, self.address, connectable=True
                )
                if ble_device is None:
                    _LOGGER.debug("Ooni device %s not in range", self.address)
                    return

                try:
                    self.client = await Client.connect(
                        device=ble_device,
                        notify_callback=self._handle_bluetooth_update,
                        disconnected_callback=self._on_disconnected,
                        max_attempts=CONNECT_MAX_ATTEMPTS,
                    )
                    _LOGGER.debug("Connected to Ooni device %s", self.address)
                    # Refresh entities so the connectivity sensor flips on now;
                    # measurements follow on the next notification.
                    self.hass.loop.call_soon_threadsafe(self.async_update_listeners)
                except BleakOutOfConnectionSlotsError as err:
                    # A Bluetooth proxy is out of slots; back off much longer
                    # because the slot stays reserved for a while after a drop.
                    self.client = None
                    _LOGGER.warning(
                        "Bluetooth proxy out of connection slots, waiting %ss: %s",
                        OUT_OF_SLOTS_RETRY_INTERVAL,
                        err,
                    )
                    self._last_connect_attempt = (
                        time.monotonic()
                        + OUT_OF_SLOTS_RETRY_INTERVAL
                        - MIN_RETRY_INTERVAL
                    )
                except asyncio.CancelledError:
                    raise
                except Exception as err:  # noqa: BLE001 - backend raises broadly
                    self.client = None
                    _LOGGER.debug("Ooni connection attempt failed: %s", err)
        finally:
            self._connecting = False
            if not self.connected:
                self.client = None
                # Honor the full cooldown from the actual failure time, unless an
                # out-of-slots backoff already pushed the timestamp further out.
                self._last_connect_attempt = max(
                    self._last_connect_attempt, time.monotonic()
                )

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
