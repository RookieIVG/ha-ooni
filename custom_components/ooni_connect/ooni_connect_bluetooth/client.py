from __future__ import annotations

import logging
from asyncio import Future
from collections.abc import Callable
from typing import TypeVar

from bleak import BleakClient
from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import establish_connection

from .const import MainService
from .exceptions import DecodeError
from .packets import Packet, PacketNotify
from .services import NotifyCharacteristic

_LOGGER = logging.getLogger(__name__)

_PacketNotifyType = TypeVar("_PacketNotifyType", bound=PacketNotify)


class Client:
    def __init__(
        self, client: BleakClient, notify_callback: Callable[[Packet], None] | None
    ) -> None:
        self.bleak_client = client
        self._notify_callbacks: list[Callable[[Packet], None]] = []
        if notify_callback:
            self._notify_callbacks.append(notify_callback)

    @property
    def is_connected(self) -> bool:
        return self.bleak_client.is_connected

    def notify_callbacks(self, packet: Packet) -> None:
        for callback in self._notify_callbacks:
            callback(packet)

    async def _start_notify(self) -> None:
        def notify_data(
            char_specifier: BleakGATTCharacteristic, data: bytearray
        ) -> None:
            try:
                packet_data = NotifyCharacteristic.decode(data)
                packet = PacketNotify.decode(packet_data)
            except DecodeError as exc:
                # FIX: previously `packet` stayed unbound here and the code fell
                # through to notify_callbacks(packet), raising NameError inside
                # the BLE notify handler. Bail out cleanly instead.
                _LOGGER.error("Failed to decode %s: %s", data, exc)
                return

            _LOGGER.debug("Notify: %s", packet)
            self.notify_callbacks(packet)

        await self.bleak_client.start_notify(MainService.notify.uuid, notify_data)

    @staticmethod
    async def connect(
        device: BLEDevice,
        notify_callback: Callable[[Packet], None] | None = None,
        disconnected_callback: Callable[[], None] | None = None,
    ) -> Client:
        def _disconnected_callback(client: BleakClient) -> None:
            _LOGGER.info("Device disconnected %s", client.address)
            if disconnected_callback:
                disconnected_callback()

        bleak_client = await establish_connection(
            BleakClient,
            device=device,
            name="Ooni Connect Connection",
            disconnected_callback=_disconnected_callback,
        )
        try:
            client = Client(bleak_client, notify_callback)
            await client._start_notify()
        except Exception:
            # FIX: previously this swallowed the error (`pass`) and returned a
            # client wrapping an already-disconnected BleakClient. Re-raise so
            # the caller (e.g. the Home Assistant coordinator) can retry.
            await bleak_client.disconnect()
            raise
        return client

    async def disconnect(self) -> None:
        await self.bleak_client.disconnect()

    async def read(self, packet_type: type[_PacketNotifyType]) -> _PacketNotifyType:
        # NOTE: this calls self.request(...), which is not implemented on Client
        # (only PacketNotify.request exists and raises NotImplementedError).
        # read() therefore cannot work until a request/write path is added.
        # It is unused by the Home Assistant integration, which relies purely on
        # notifications, but should be implemented or removed for completeness.
        result: Future[_PacketNotifyType] = Future()

        def _callback(packet: Packet) -> None:
            if isinstance(packet, packet_type):
                if not result.cancelled() and not result.done():
                    result.set_result(packet)

        self._notify_callbacks.append(_callback)
        try:
            await self.request(packet_type)  # type: ignore[attr-defined]
            return await result
        finally:
            self._notify_callbacks.remove(_callback)
