"""Config flow for Senertec energy systems integration."""

from __future__ import annotations

import logging
from typing import Any, Mapping

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, selector
from homeassistant.helpers.selector import SelectOptionDict
from senertec.client import senertec

from .const import DEVICES, DOMAIN, SELECTED_DEVICES, STEP_USER_DATA_SCHEMA
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
    devices = await hass.async_add_executor_job(client.getUnits)
    if len(devices) == 0:
        raise NoUnits
    await hass.async_add_executor_job(client.logout)
    return {
        DEVICES: [
            SelectOptionDict(label=f"{dev.model} ({dev.serial})", value=dev.serial)
            for dev in devices
        ]
    }


class SenertecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Senertec energy systems integration."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the Cloudflare config flow."""
        self.senertec_config: dict[str, Any] = {}

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
    ) -> config_entries.ConfigFlowResult:
        errors = {}
        if user_input:
            try:
                self.senertec_config.update(
                    await validate_connection(self.hass, user_input)
                )
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
            if not errors:
                self.senertec_config.update(user_input)
                await self.async_set_unique_id(self.senertec_config[CONF_EMAIL])
                if self.source != config_entries.SOURCE_REAUTH:
                    self._abort_if_unique_id_configured()
                    return await self.async_step_devices()
                self._abort_if_unique_id_mismatch()
                return self.async_update_reload_and_abort(
                    self._get_reauth_entry(),
                    data_updates=user_input,
                )

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_devices(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        if user_input:
            self.senertec_config.update(user_input)
            return self.async_create_entry(
                title=f"Senertec - {self.senertec_config[CONF_EMAIL]}",
                data=self.senertec_config,
            )
        return self.async_show_form(
            step_id="devices",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        SELECTED_DEVICES, default=False
                    ): selector.SelectSelector(
                        selector.SelectSelectorConfig(
                            options=self.senertec_config[DEVICES],
                            mode=selector.SelectSelectorMode.LIST,
                            multiple=True,
                        ),
                    )
                }
            ),
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
