import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_MAC
from .const import DOMAIN

class OoniConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(
                title=f"Ooni {user_input[CONF_MAC]}",
                data={CONF_MAC: user_input[CONF_MAC]},
            )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({
                vol.Required(CONF_MAC): str,
            }),
        )
