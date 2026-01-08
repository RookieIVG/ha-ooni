import logging
from datetime import timedelta
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.core import HomeAssistant
from bleak import BleakScanner, BleakError
from .const import DEFAULT_SCAN_INTERVAL
from .ooni_connect_bluetooth.client import OoniBluetooth

_LOGGER = logging.getLogger(__name__)

class OoniCoordinator(DataUpdateCoordinator):
    """Coordinator für Ooni BLE Integration mit Auto-Reconnect"""

    def __init__(self, hass: HomeAssistant, mac: str):
        self._mac = mac
        self._data = {}
        self._connected_device = None
        self._connected = False

        # Callback für Notifications
        def _notify_callback(data: dict):
            self._data = data

        self._ooni = OoniBluetooth(mac, _notify_callback)

        super().__init__(
            hass,
            _LOGGER,
            name="Ooni BLE Coordinator",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )

    async def _async_update_data(self):
        """Scan, Connect und Daten abholen mit Auto-Reconnect."""
        try:
            # 🔹 Scan nach Device
            devices = await BleakScanner.discover()
            device = next(
                (d for d in devices if d.address.lower() == self._mac.lower()), None
            )

            if device is None:
                self._connected = False
                raise UpdateFailed(f"Ooni device {self._mac} not found during scan")

            self._connected_device = device

            # 🔹 Connect
            if not self._connected:
                try:
                    await self._ooni.connect(device)
                    self._connected = True
                    _LOGGER.info(f"Ooni BLE device {self._mac} connected")
                except BleakError as err:
                    self._connected = False
                    raise UpdateFailed(f"Ooni connect failed: {err}")

            # 🔹 Daten werden über Callback automatisch aktualisiert
            return self._data

        except Exception as err:
            self._connected = False
            raise UpdateFailed(f"Ooni update failed: {err}") from err

    @property
    def is_connected(self):
        """Status ob BLE verbunden."""
        return self._connected

    async def async_disconnect(self):
        """BLE Gerät sauber trennen."""
        if self._connected_device and self._connected:
            try:
                await self._ooni.disconnect()
            except Exception:
                pass
            finally:
                self._connected = False
