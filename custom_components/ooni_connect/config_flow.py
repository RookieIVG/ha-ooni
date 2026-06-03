"""Config flow for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_ble_device_from_address,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Short timeout for the one-shot reachability test during setup.
_CONFIG_CHECK_TIMEOUT = 10


def _is_ooni(name: str | None) -> bool:
    """Return True if the advertised name looks like an Ooni device."""
    return name is not None and "OONI" in name.upper()


class OoniConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ooni Connect Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovered_devices: dict[str, str] = {}
        self._address: str = ""
        self._name: str = ""
        self._rssi: int | None = None

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()
        self._migrate_legacy_entry(discovery_info.address)

        device_name = discovery_info.name or discovery_info.address
        if not _is_ooni(device_name):
            return self.async_abort(reason="not_ooni_device")

        self._address = discovery_info.address
        self._name = device_name
        self._rssi = discovery_info.rssi
        self.context["title_placeholders"] = {"name": device_name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        if user_input is not None:
            return await self.async_step_connection_check()

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._name},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user (manual search)."""
        if user_input is not None:
            self._address = user_input[CONF_ADDRESS]
            self._name = self._discovered_devices[self._address]
            await self.async_set_unique_id(self._address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            for info in async_discovered_service_info(self.hass):
                if info.address == self._address:
                    self._rssi = info.rssi
                    break
            return await self.async_step_connection_check()

        # Scan for Ooni devices that aren't configured yet.
        current_addresses = self._async_current_ids()
        for discovery_info in async_discovered_service_info(self.hass):
            address = discovery_info.address
            if address in current_addresses:
                continue
            name = discovery_info.name or address
            if _is_ooni(name):
                self._discovered_devices[address] = name

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {vol.Required(CONF_ADDRESS): vol.In(self._discovered_devices)}
            ),
        )

    async def async_step_connection_check(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Test reachability once and warn the user if the connection fails."""
        # User acknowledged the warning -> create the entry anyway.
        if user_input is not None:
            return self._create_entry()

        # Don't kick a live connection held by an existing coordinator.
        if self._is_already_connected():
            return self._create_entry()

        connection_ok, error_message = await self._try_connect()
        if connection_ok:
            return self._create_entry()

        _LOGGER.warning(
            "Config flow connection check failed for %s (%s): %s",
            self._name,
            self._address,
            error_message,
        )
        # No data_schema + errors would hide the description, so the guidance
        # lives entirely in the description text.
        self._set_confirm_only()
        return self.async_show_form(
            step_id="connection_check",
            description_placeholders={
                "name": self._name,
                "rssi": str(self._rssi) if self._rssi is not None else "unknown",
                "error": error_message,
            },
        )

    def _create_entry(self) -> FlowResult:
        """Create the config entry."""
        return self.async_create_entry(
            title=self._name,
            data={CONF_ADDRESS: self._address, CONF_NAME: self._name},
        )

    def _migrate_legacy_entry(self, address: str) -> None:
        """Backfill unique_id on an older entry that was created without one."""
        for entry in self._async_current_entries(include_ignore=False):
            if entry.data.get(CONF_ADDRESS) == address and entry.unique_id is None:
                self.hass.config_entries.async_update_entry(
                    entry, unique_id=address
                )

    def _is_already_connected(self) -> bool:
        """Return True if an existing coordinator already holds this connection."""
        for coordinator in self.hass.data.get(DOMAIN, {}).values():
            if (
                getattr(coordinator, "address", None) == self._address
                and getattr(coordinator, "connected", False)
            ):
                return True
        return False

    async def _try_connect(self) -> tuple[bool, str]:
        """Attempt a single short BLE connection. Returns (ok, error_message)."""
        from bleak import BleakClient
        from bleak_retry_connector import establish_connection

        ble_device = async_ble_device_from_address(
            self.hass, self._address, connectable=True
        )
        if ble_device is None:
            return False, f"Device {self._address} not found by the Bluetooth scanner"

        client: BleakClient | None = None
        try:
            async with asyncio.timeout(_CONFIG_CHECK_TIMEOUT):
                client = await establish_connection(
                    BleakClient,
                    device=ble_device,
                    name="Ooni Config Check",
                    max_attempts=1,
                )
            if client.is_connected:
                return True, ""
            return False, "Connection established but the device dropped immediately"
        except asyncio.TimeoutError:
            return False, f"Connection timed out after {_CONFIG_CHECK_TIMEOUT} seconds"
        except Exception as err:  # noqa: BLE001
            # Trim the verbose advice suffix bleak-retry-connector appends.
            message = str(err)
            if ": Interference/range" in message:
                message = message.split(": Interference/range")[0]
            return False, message
        finally:
            if client is not None:
                try:
                    await client.disconnect()
                except Exception:  # noqa: BLE001
                    pass
