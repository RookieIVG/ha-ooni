"""Ooni Connect main module"""

from bleak.uuids import register_uuids

from .services import Service

SUPPORTED_DEVICES = {
    "Ooni_DT_Hub"
}

register_uuids(
    {service.uuid: f"Ooni Connect {service.__name__}" for service in Service.registry.values()}
)

register_uuids(
    {
        char.uuid: f"Ooni Connect {service.__name__} {char.name}"
        for service in Service.registry.values()
        for char in service.characteristics()
    }
)
