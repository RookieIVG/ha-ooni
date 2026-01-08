from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import IntEnum
from typing import Self

from .exceptions import DecodeError
from enum import Enum

def from_scaled_nullable(data: bytes, scale: float, null: int) -> float | None:
    if (value := from_nullable(data, null)) is None:
        return None
    return value / scale


def to_scaled_nullable(data: float | None, length: int, scale: float, null: int) -> bytes:
    if data is None:
        return null.to_bytes(length, "big")
    return round(data * scale).to_bytes(length, "big")


def from_nullable(data: bytes, null: int) -> int | None:
    value = int.from_bytes(data, "big")
    if value == null:
        return None
    return value


def from_nullable_enum(data: bytes, enum: type[IntEnum], null: int) -> int | None:
    if (value := from_nullable(data, null)) is None:
        return None
    try:
        return enum(value)
    except ValueError:
        return value


def to_nullable(data: int | None, length: int, null: int) -> bytes:
    if data is None:
        return null.to_bytes(length, "big")
    return data.to_bytes(length, "big")




@dataclass
class Packet:
    @classmethod
    def decode(cls, data: bytes) -> Self:
        raise NotImplementedError()

    def encode(self) -> bytes:
        raise NotImplementedError()

@dataclass
class TemperatureUnit(str, Enum):
    CELCIUS = "C"
    FARENHEIT = "F"


@dataclass
class PacketNotify(Packet):
    battery: int
    ambient_a: int
    ambient_b: int
    probe_p1: int
    probe_p2: int
    probe_p1_connected: bool = False
    probe_p2_connected: bool = False
    eco_mode: bool = False
    temperature_unit: TemperatureUnit = field(default_factory=lambda: TemperatureUnit.CELCIUS)


    def __init_subclass__(cls, /, **kwargs):
        super().__init_subclass__(**kwargs)


    @classmethod
    def decode(cls, data: bytes) -> Self:
        if len(data) < 6:
            raise DecodeError("Packet too short")

        #int_0 = struct.unpack('<I', data[0:4])[0]  # 4-byte int: 20
        flag = data[0]  # Single byte: 0x14 = 20
        ambient_a = struct.unpack('<H', data[2:4])[0] # 2-byte int: 88
        ambient_b = struct.unpack('<H', data[4:6])[0] # 2-byte int: 31868
        probe_p1 = struct.unpack('<H', data[6:8])[0] # 2-byte int: 26
        probe_p2 = struct.unpack('<H', data[8:10])[0] # 2-byte int: 26
        battery = data[10]  # Byte at position 10: 0x58 = 88 (battery percentage)
        probe_p1_connected = (flag & 0x04) >> 2  # Probe P1 flag
        probe_p2_connected = (flag & 0x08) >> 3  # Probe P2 flag
        eco_mode = (flag & 0x80) >> 7  # Eco mode flag
        temperature_unit = TemperatureUnit.CELCIUS if (flag & 0x01) else TemperatureUnit.FARENHEIT  # Temperature unit

        return cls(
            battery=battery,
            ambient_a=ambient_a,
            ambient_b=ambient_b,
            probe_p1=probe_p1,
            probe_p2=probe_p2,
            probe_p1_connected=bool(probe_p1_connected),
            probe_p2_connected=bool(probe_p2_connected),
            eco_mode=bool(eco_mode),
            temperature_unit=temperature_unit,
        )

    @classmethod
    def request(cls) -> bytes:
        raise NotImplementedError
