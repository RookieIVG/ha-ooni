"""Constants"""

from dataclasses import dataclass
from typing import ClassVar

# FIX: the upstream file imported NotifyCharacteristic via the absolute path
# `from ooni_connect_bluetooth.services import ...`, which breaks once the
# package is vendored under a different import path. Use a relative import.
from .services import NotifyCharacteristic, Service


class MainService(Service):
    uuid = "0000cee0-0000-1000-8000-00805f9b34fb"
    notify = NotifyCharacteristic()  # pylint: disable=no-value-for-parameter


@dataclass
class ManufacturerData:
    company: ClassVar[int] = 0x879A

    @staticmethod
    def decode(data: bytes):
        return ManufacturerData()
