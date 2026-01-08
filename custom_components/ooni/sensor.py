from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from .const import DOMAIN

SENSORS = {
    "temperature": ("Ofen Temperatur", "°C"),
    "target_temperature": ("Ziel Temperatur", "°C"),
    "battery": ("Akku", "%"),
    "state": ("Status", None),
}

async def async_setup_entry(hass, entry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        OoniSensor(coordinator, key, name, unit)
        for key, (name, unit) in SENSORS.items()
    ]

    async_add_entities(entities)

class OoniSensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, key, name, unit):
        super().__init__(coordinator)
        self._key = key
        self._attr_name = name
        self._attr_native_unit_of_measurement = unit
        self._attr_unique_id = f"ooni_{coordinator._mac}_{key}"

    @property
    def native_value(self):
        return self.coordinator.data.get(self._key)
