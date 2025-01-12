from datetime import timedelta
import logging
import time

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL
from homeassistant.core import ServiceCall
from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from senertec.client import canipValue, senertec
from senertec.lang import lang

from .const import (
    CONF_LANG,
    DEFAULT_LANG,
    DEFAULT_POLL_INTERVAL,
    DOMAIN,
    SENERTEC_POLL_SERVICE,
)

_LOGGER = logging.getLogger(__name__)


class SenertecCoordinator(DataUpdateCoordinator):
    """A Senertec energy systems wrapper class."""

    def __init__(self, hass, config_entry: ConfigEntry, supportedItems):
        """Initialize the Senertec energy system."""
        super().__init__(
            hass,
            _LOGGER,
            # Name of the data. For logging purposes.
            name=DOMAIN,
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(
                minutes=config_entry.options.get(
                    CONF_SCAN_INTERVAL, DEFAULT_POLL_INTERVAL
                )
            ),
        )
        language = self.config_entry.options.get(CONF_LANG, DEFAULT_LANG)
        self.senertec_client = senertec(lang[language])
        self.senertec_client.messagecallback = self._ws_callback
        self.supportedItems = supportedItems
        # self._hass = hass

    def _fetch(self):
        _LOGGER.debug("Starting Senertec energy system connection")
        try:
            login = self.senertec_client.login(
                self.config_entry.data[CONF_EMAIL],
                self.config_entry.data[CONF_PASSWORD],
            )
            if not login:
                raise ConfigEntryAuthFailed("Credentials seem to be expired or invalid")
            init = self.senertec_client.init()
            if not init:
                _LOGGER.error("Login/init failed")
                return
            units = self.senertec_client.getUnits()
            if len(units) == 0:
                _LOGGER.error("No devices were found")
                return
            for unit in units:
                self.data[unit.serial] = {}
                self.data[unit.serial]["sensors"] = {}
                self.data[unit.serial]["device"] = unit
                if not self.senertec_client.connectUnit(unit.serial):
                    _LOGGER.error("Connecting to device: %s failed", unit.serial)
                    continue
                errors = self.senertec_client.getErrors()
                self.data[unit.serial]["errors"] = errors
                self._request_sensors()
                self.senertec_client.disconnectUnit()
        except Exception as ex:
            _LOGGER.error(ex.with_traceback())

    def _request_sensors(self):
        _LOGGER.debug("Polling senertec sensors")
        try:
            self.senertec_client.request(self.supportedItems)
            # wait 5 seconds for websocket to receive data
            time.sleep(5)
        except Exception as ex:
            _LOGGER.error(ex)

    async def async_setup(self) -> None:
        """Set up senertec."""

        async def request_update(call: ServiceCall) -> None:
            """Request update."""
            await self.async_request_refresh()

        self.hass.services.async_register(DOMAIN, SENERTEC_POLL_SERVICE, request_update)

    async def _async_update_data(self):
        """Update senertec data."""
        _LOGGER.debug("Starting data update")
        self.data = {}
        await self.hass.async_add_executor_job(self._fetch)
        await self._stop()
        _LOGGER.debug("Finished data update")
        return self.data

    async def _stop(self):
        _LOGGER.debug("Stopping Senertec energy system connection")
        await self.hass.async_add_executor_job(self.senertec_client.logout)

    def _ws_callback(self, value: canipValue):
        _LOGGER.debug("Received senertec sensor value")
        # append the received value to the correct device
        self.data[value.deviceSerial]["sensors"][value.sourceDatapoint] = value
