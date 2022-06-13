"""Config flow for Senertec energy systems integration."""
from __future__ import annotations
import json

import logging
import os
import voluptuous as vol
from typing import Any

from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
)

from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError
from homeassistant.data_entry_flow import FlowResult
from senertec.client import senertec


from .const import DOMAIN, DEFAULT_NAME, STEP_USER_DATA_SCHEMA
from .SenertecOptionsFlow import SenertecOptionsFlow

_LOGGER = logging.getLogger(__name__)


async def validate_connection(hass: HomeAssistant, data: dict[str, Any]):
    """Validate the user input allows us to connect.

    Data has the keys from STEP_USER_DATA_SCHEMA with values provided by the user.
    """

    _LOGGER.debug("Trying to connect to senertec during setup")
    file = await hass.async_add_executor_job(
        open,
        "/config/custom_components/senertec_hassio/productGroups.json",
    )
    supportedItems = json.load(file)
    file.close()
    client = senertec(
        dataNames=supportedItems, email=data[CONF_EMAIL], password=data[CONF_PASSWORD]
    )
    if not await hass.async_add_executor_job(client.login):
        raise InvalidAuth
    await hass.async_add_executor_job(client.init)
    units = await hass.async_add_executor_job(client.getUnits)
    await hass.async_add_executor_job(client.connectUnit, units[0].serial)
    await hass.async_add_executor_job(client.logout)
    _LOGGER.debug("Successfully connected to senertec during setup.")
    lst = []
    for a in client.boards:
        points = []
        for b in a.datapoints:
            points.append({"sourceId": b.sourceId, "friendlyName": b.friendlyName})
        lst.append({"boardname": a.boardName, "datapoints": points})
    # Return info that you want to store in the config entry.
    data["model"] = units[0].model
    data["serial"] = units[0].serial
    data["sensors"] = lst
    return data


class SenertecConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Senertec energy systems integration."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:

        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=STEP_USER_DATA_SCHEMA
            )

        errors = {}

        try:
            info = await validate_connection(self.hass, user_input)
        except CannotConnect:
            errors["base"] = "cannot_connect"
        except InvalidAuth:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(info["serial"])
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title=DEFAULT_NAME, data=info)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_sensors(self, user_input=None):
        if not user_input:
            sensors = {}
            for board in self.hass.data["sensors"]:
                for point in board:
                    sensors[vol.Optional(point["sourceId"], default=True)] = bool
            return self.async_show_form(
                step_id="sensors", data_schema=vol.Schema(sensors)
            )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SenertecOptionsFlow(config_entry)


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
