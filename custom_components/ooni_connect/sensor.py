import logging
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.const import PERCENTAGE, UnitOfTemperature
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Wir definieren hier die Sensoren mit festen Einheiten
SENSOR_TYPES: tuple[SensorEntityDescription, ...] = (
    SensorEntityDescription(
        key="battery",
        name="Batterie",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="ambient_a",
        name="Umgebungstemperatur A",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="ambient_b",
        name="Umgebungstemperatur B",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="probe_p1",
        name="Sonde 1",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    SensorEntityDescription(
        key="probe_p2",
        name="Sonde 2",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Sensoren einrichten."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OoniTemperatureSensor(coordinator, description)
        for description in SENSOR_TYPES
    )

class OoniTemperatureSensor(CoordinatorEntity, SensorEntity):
    """Repräsentiert einen Ooni Sensor."""

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": getattr(coordinator, "device_name", "Ooni Hub"),
            "manufacturer": "Ooni",
        }

    @property
    def native_value(self):
        """Gibt den Wert vom Gerät 1:1 zurück."""
        if not self.coordinator.data:
            return None
        
        val = getattr(self.coordinator.data, self.entity_description.key, None)
        
        # Falls es der Einheiten-Sensor ist, extrahieren wir den Buchstaben (C/F)
        if self.entity_description.key == "temperature_unit" and val is not None:
            return getattr(val, "value", str(val))
            
        return val
