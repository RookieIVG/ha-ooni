from datetime import timedelta
import logging
from typing import Any

from homeassistant.components.bluetooth import async_ble_device_from_address
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

class OoniConnectCoordinator(DataUpdateCoordinator[Any]):
    """Klasse zur Verwaltung der Datenabfrage von Ooni Connect."""

    def __init__(self, hass, address, name):
        """Initialisierung."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=10),
        )
        self.address = address
        self.device_name = name
        self.client = None

    async def _async_update_data(self) -> Any:
        """Daten vom Gerät abrufen."""
        # Import innerhalb der Funktion, um 'Blocking Call' Fehler zu vermeiden
        # Wir versuchen beide gängigen Namen, falls einer nicht existiert
        try:
            from ooni_connect_bluetooth.client import OoniBluetoothClient as ClientClass
        except ImportError:
            try:
                from ooni_connect_bluetooth.client import OoniConnectBluetoothClient as ClientClass
            except ImportError:
                raise UpdateFailed("Konnte Client-Klasse in ooni_connect_bluetooth nicht finden.")

        try:
            # Client initialisieren
            if self.client is None:
                self.client = ClientClass(self.address)

            # Bluetooth Gerät in HA finden
            ble_device = async_ble_device_from_address(self.hass, self.address)
            if not ble_device:
                raise UpdateFailed(f"Gerät mit Adresse {self.address} nicht gefunden")

            # Verbinden (falls nötig) und Daten lesen
            if not self.client.is_connected:
                await self.client.connect()
            
            # Daten abrufen
            data = await self.client.get_data()
            return data
            
        except Exception as err:
            # Fehler loggen, aber Verbindung für nächsten Versuch sauber halten
            _LOGGER.error("Fehler bei Ooni Update: %s", err)
            raise UpdateFailed(f"Verbindungsfehler: {err}")
