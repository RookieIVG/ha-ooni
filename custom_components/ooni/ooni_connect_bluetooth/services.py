from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar, Generic, TypeVar

CharacteristicType = TypeVar("CharacteristicType")


def pretty_name(name: str):
    data = name.split("_")
    return " ".join(f"{part[0].upper()}{part[1:]}" for part in data)


@dataclass
class Characteristic(Generic[CharacteristicType]):
    uuid: str
    name: str = ""
    registry: ClassVar[dict[str, Characteristic]] = {}

    def __set_name__(self, _, name: str):
        self.name = pretty_name(name)

    def __post_init__(self):
        self.registry[self.uuid] = self

    @classmethod
    def decode(cls, data: bytes) -> CharacteristicType:
        raise NotImplementedError(f"Decoding of {type(cls)} is not implemented")

    @classmethod
    def encode(cls, data: CharacteristicType) -> bytes:
        raise NotImplementedError(f"Encoding of {type(cls)} is not implemented")


class Service:
    uuid: ClassVar[str]
    registry: ClassVar[dict[str, type[Service]]] = {}

    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.registry[cls.uuid] = cls

    @classmethod
    def characteristics(cls):
        for value in vars(cls).values():
            if isinstance(value, Characteristic):
                yield value


@dataclass
class NotifyCharacteristic(Characteristic[bytes]):
    uuid: ClassVar[str] = "69400002-b5a3-f393-e0a9-e50e24dcca99"

    @staticmethod
    def decode(data: bytes) -> bytes:
        return data

    @staticmethod
    def encode(data: bytes) -> bytes:
        return data
