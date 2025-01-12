"""Config flow for Senertec energy systems integration."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
from senertec.client import senertec

from .const import DOMAIN, STEP_USER_DATA_SCHEMA
from .OptionsFlowHandler import OptionsFlowHandler

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """
    _LOGGER.debug("Trying to connect to senertec during setup")
    client = senertec()
    if not await hass.async_add_executor_job(
        client.login, data[CONF_EMAIL], data[CONF_PASSWORD]
    ):
        raise InvalidAuth
    if not await hass.async_add_executor_job(client.init):
        raise InitFailed
    units = await hass.async_add_executor_job(client.getUnits)
    if len(units) == 0:
        raise NoUnits
    await hass.async_add_executor_job(client.logout)
    _LOGGER.debug("Successfully connected to senertec during setup")


class SenertecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Senertec energy systems integration."""

    VERSION = 1

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> config_entries.ConfigFlowResult:
        """Perform reauth upon an login authentication error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        """Dialog that informs the user that reauth is required."""
        if user_input is None:
            return self.async_show_form(
                step_id="reauth_confirm",
                data_schema=vol.Schema({}),
            )
        return await self.async_step_user()

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            await validate_connection(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except NoUnits:
            errors["base"] = "no_units"
        except InitFailed:
            errors["base"] = "init_failed"
        except Exception:
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(user_input[CONF_EMAIL])
            if self.source == config_entries.SOURCE_REAUTH:
                self._abort_if_unique_id_mismatch()
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=f"Senertec - {user_input[CONF_EMAIL]}", data=user_input
            )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> OptionsFlowHandler:
        """Create the options flow."""
        return OptionsFlowHandler()


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""


class NoUnits(HomeAssistantError):
    """Error to indicate there were no energy units found."""


class InitFailed(HomeAssistantError):
    """Error to indicate the initialization failed."""
