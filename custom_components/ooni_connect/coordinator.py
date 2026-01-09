from datetime import timedelta
import logging
import asyncio
from typing import Any

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class OoniConnectCoordinator(DataUpdateCoordinator[Any]):
    """Verwaltung der Ooni DT Hub Verbindung mit schnellem Start."""

    def __init__(self, hass: HomeAssistant, address: str, name: str):
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=60),
        )
        self.address = address
        self.device_name = name
        self.client = None
        self._last_data = None
        self._lock = asyncio.Lock()
        self._connection_task = None

    def _handle_bluetooth_update(self, data: Any) -> None:
        """Callback für Datenpakete."""
        _LOGGER.debug("Ooni Daten empfangen: %s", data)
        self._last_data = data
        self.async_set_updated_data(data)

    def _on_disconnected(self) -> None:
        """Callback bei Verbindungsverlust."""
        _LOGGER.warning("Ooni Verbindung getrennt")
        self.client = None

    async def _async_update_data(self) -> Any:
        """Wird von HA regelmäßig aufgerufen."""
        # Wenn kein Task läuft und wir nicht verbunden sind, starte Verbindungsversuch im Hintergrund
        if self.client is None or not self.client.is_connected:
            if self._connection_task is None or self._connection_task.done():
                self._connection_task = self.hass.async_create_task(self._connect_in_background())
        
        return self._last_data

    async def _connect_in_background(self) -> None:
        """Versucht die Verbindung im Hintergrund aufzubauen, ohne HA zu blockieren."""
        from ooni_connect_bluetooth.client import Client

        async with self._lock:
            ble_device = async_ble_device_from_address(self.hass, self.address)
            if not ble_device:
                _LOGGER.debug("Ooni nicht erreichbar (Hintergrund)")
                return

            try:
                _LOGGER.info("Hintergrund-Verbindung zu Ooni wird aufgebaut...")
                # Timeout für den Connect, damit der Task nicht ewig hängt
                async with asyncio.timeout(20):
                    self.client = await Client.connect(
                        device=ble_device,
                        notify_callback=self._handle_bluetooth_update,
                        disconnected_callback=self._on_disconnected
                    )
                _LOGGER.info("Ooni im Hintergrund erfolgreich verbunden")
            except Exception as err:
                _LOGGER.debug("Hintergrund-Verbindung fehlgeschlagen (Gerät wohl aus): %s", err)
                self.client = None
