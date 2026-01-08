"""Constants"""

from dataclasses import dataclass
from typing import ClassVar

from .services import NotifyCharacteristic

from .services import Service


class MainService(Service):
    uuid = "0000cee0-0000-1000-8000-00805f9b34fb"
    notify = NotifyCharacteristic() # pylint: disable=no-value-for-parameter


@dataclass
class ManufacturerData:
    company: ClassVar[int] = 0x879A

    @staticmethod
    def decode(data: bytes):
        return ManufacturerData()
