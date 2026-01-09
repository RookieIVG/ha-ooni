from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

# Hier fügen wir den neuen Sensor "status_connected" hinzu
BINARY_SENSORS: tuple[BinarySensorEntityDescription, ...] = (
    BinarySensorEntityDescription(
        key="status_connected",
        name="Bluetooth Verbindung",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="probe_p1_connected",
        name="Sonde 1 Verbunden",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="probe_p2_connected",
        name="Sonde 2 Verbunden",
        device_class=BinarySensorDeviceClass.CONNECTIVITY,
    ),
    BinarySensorEntityDescription(
        key="eco_mode",
        name="Eco Modus",
        device_class=BinarySensorDeviceClass.POWER,
    ),
)

async def async_setup_entry(hass, entry, async_add_entities):
    """Richtet die binären Sensoren ein."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        OoniBinarySensor(coordinator, description)
        for description in BINARY_SENSORS
    )

class OoniBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Repräsentiert einen binären Sensor (Ja/Nein)."""

    def __init__(self, coordinator, description):
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{coordinator.address}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.address)},
            "name": coordinator.device_name,
            "manufacturer": "Ooni",
        }

    @property
    def is_on(self) -> bool:
        """Entscheidet, ob der Sensor 'An' oder 'Aus' ist."""
        
        # 1. Spezialfall: Der Verbindungs-Sensor selbst
        if self.entity_description.key == "status_connected":
            # Wenn das letzte Update erfolgreich war, sind wir verbunden
            return self.coordinator.last_update_success

        # 2. Alle anderen Sensoren (Sonden, Eco Mode)
        # Wenn wir gar keine Daten haben (z.B. ganz am Anfang oder offline), sind sie aus/falsch
        if not self.coordinator.data:
            return None # Oder False, je nach Geschmack
        
        # Wert aus dem Daten-Objekt holen
        return getattr(self.coordinator.data, self.entity_description.key, False)

    @property
    def available(self) -> bool:
        """Wann ist der Sensor überhaupt verfügbar?"""
        # Der Verbindungssensor ist IMMER verfügbar (er zeigt ja an, ob es geht oder nicht)
        if self.entity_description.key == "status_connected":
            return True
        
        # Alle anderen Sensoren sind nur verfügbar, wenn wir Daten haben
        return self.coordinator.last_update_success
