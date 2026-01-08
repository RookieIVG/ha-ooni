from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN, PLATFORMS

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    from .coordinator import OoniCoordinator

    coordinator = OoniCoordinator(
        hass,
        entry.data["mac"],
    )

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
