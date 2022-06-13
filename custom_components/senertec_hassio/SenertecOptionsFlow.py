import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_SCAN_INTERVAL
from .const import DOMAIN, DEFAULT_POLL_INTERVAL, DEFAULT_LANG, CONF_LANG, LANGUAGES
from senertec.lang import lang

class SenertecOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        """Initialize senertec options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any]):
        """Manage the options."""
        return await self.async_step_user(user_input)

    async def async_step_user(self, user_input):
        """Handle a flow initialized by the user."""
        errors = {}
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = {
            vol.Optional(
                CONF_LANG,
                default=self.config_entry.options.get(CONF_LANG, DEFAULT_LANG),
            ): vol.In(LANGUAGES),
            vol.Optional(
                CONF_SCAN_INTERVAL,
                default=self.config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_POLL_INTERVAL
                ),
            ): int
        }

        return self.async_show_form(
            step_id="init", data_schema=vol.Schema(options), errors=errors
        )
