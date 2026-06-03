"""Config flow for the Ooni Connect Bluetooth integration."""

from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.const import CONF_ADDRESS, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


def _is_ooni(name: str | None) -> bool:
    """Return True if the advertised name looks like an Ooni device."""
    return name is not None and "OONI" in name.upper()


class OoniConnectConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Ooni Connect Bluetooth."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the config flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, str] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> FlowResult:
        """Handle bluetooth discovery."""
        await self.async_set_unique_id(discovery_info.address)
        self._abort_if_unique_id_configured()

        device_name = discovery_info.name or discovery_info.address
        if not _is_ooni(device_name):
            return self.async_abort(reason="not_ooni_device")

        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": device_name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm discovery."""
        assert self._discovery_info is not None
        name = self._discovery_info.name or self._discovery_info.address

        if user_input is not None:
            return self.async_create_entry(
                title=name,
                data={
                    CONF_ADDRESS: self._discovery_info.address,
                    CONF_NAME: name,
                },
            )

        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": name},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle a flow initialized by the user (manual search)."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            # Guard against adding the same device twice.
            await self.async_set_unique_id(address, raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=self._discovered_devices[address],
                data={
                    CONF_ADDRESS: address,
                    CONF_NAME: self._discovered_devices[address],
                },
            )

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
