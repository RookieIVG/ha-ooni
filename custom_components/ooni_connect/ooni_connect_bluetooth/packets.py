from __future__ import annotations

import struct
from dataclasses import dataclass, field
from enum import Enum, IntEnum
from typing import Self

from .exceptions import DecodeError

# --- Minimum bytes the notify payload must contain ---------------------------
# decode() reads flag=data[0], ambient_a=data[2:4], ambient_b=data[4:6],
# probe_p1=data[6:8], probe_p2=data[8:10], battery=data[10].
# The highest index accessed is 10, so we need at least 11 bytes.
_MIN_NOTIFY_LEN = 11


def from_scaled_nullable(data: bytes, scale: float, null: int) -> float | None:
    if (value := from_nullable(data, null)) is None:
        return None
    return value / scale


def to_scaled_nullable(
    data: float | None, length: int, scale: float, null: int
) -> bytes:
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


# FIX: `@dataclass` on an Enum is a no-op (and conceptually wrong); a plain
# str/Enum is what's intended here.
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
    temperature_unit: TemperatureUnit = field(
        default_factory=lambda: TemperatureUnit.CELCIUS
    )

    @classmethod
    def decode(cls, data: bytes) -> Self:
        # FIX: the previous check was `< 6`, but decode reads up to data[10].
        # A 6–10 byte payload raised struct.error / IndexError instead of a
        # DecodeError, which then crashed the notify handler in client.py.
        if len(data) < _MIN_NOTIFY_LEN:
            raise DecodeError("Packet too short")

        flag = data[0]  # e.g. 0x14
        ambient_a = struct.unpack("<H", data[2:4])[0]
        ambient_b = struct.unpack("<H", data[4:6])[0]
        probe_p1 = struct.unpack("<H", data[6:8])[0]
        probe_p2 = struct.unpack("<H", data[8:10])[0]
        battery = data[10]  # battery percentage

        probe_p1_connected = (flag & 0x04) >> 2
        probe_p2_connected = (flag & 0x08) >> 3
        eco_mode = (flag & 0x80) >> 7
        temperature_unit = (
            TemperatureUnit.CELCIUS
            if (flag & 0x10) >> 4
            else TemperatureUnit.FARENHEIT
        )

        # ---------------------------------------------------------------------
        # TODO (calibration required): the four temperature fields are returned
        # here as RAW uint16 values, not real temperatures. In a captured
        # sample ambient_b was 31868, which looks like a "no reading" sentinel
        # rather than a temperature. This module already ships the helpers to
        # handle that (`from_scaled_nullable`, `from_nullable`) but they are not
        # applied yet, so the Home Assistant integration currently displays the
        # raw numbers under a °C label.
        #
        # Once the protocol's scale factor and null sentinel are known, replace
        # the raw unpacks above with, for example:
        #
        #     SCALE = 10.0          # raw units per degree (to be measured)
        #     NULL = 0xFFFF         # sentinel for "no reading" (to be measured)
        #     ambient_a = from_scaled_nullable(data[2:4], SCALE, NULL)
        #
        # Returning None for a disconnected/idle channel lets HA show the sensor
        # as unavailable instead of a bogus value. Also consider normalising all
        # temperatures to a single unit (e.g. always Celsius) so the integration
        # doesn't have to guess based on `temperature_unit`.
        # ---------------------------------------------------------------------

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
