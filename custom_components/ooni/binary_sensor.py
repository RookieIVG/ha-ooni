from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

class OoniConnectedSensor(CoordinatorEntity, BinarySensorEntity):
    """Zeigt, ob Ooni BLE verbunden ist."""

    def __init__(self, coordinator):
        super().__init__(coordinator)
        self._attr_name = "Ooni Connected"
        self._attr_unique_id = f"ooni_{coordinator._mac}_connected"

    @property
    def is_on(self):
        return self.coordinator.is_connected


async def async_setup_entry(hass, entry, async_add_entities):
    """Binary Sensor beim Hinzufügen der Integration registrieren."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [OoniConnectedSensor(coordinator)]
    async_add_entities(entities)
