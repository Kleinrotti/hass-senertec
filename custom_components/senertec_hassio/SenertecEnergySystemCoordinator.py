import time
import logging

from senertec.client import senertec, canipError, canipValue
from senertec.lang import lang
from datetime import timedelta
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.const import CONF_SCAN_INTERVAL, CONF_EMAIL, CONF_PASSWORD

from .const import (
    DOMAIN,
    SENERTEC_POLL_SERVICE,
    DEFAULT_POLL_INTERVAL,
    DEFAULT_LANG,
    CONF_LANG,
)

_LOGGER = logging.getLogger(__name__)


class SenertecEnergySystemCoordinator(DataUpdateCoordinator):
    """A Senertec energy systems wrapper class."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry, supportedItems):
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
            update_method=self.async_update,
        )
        self.supportedItems = supportedItems
        self._canipErrors = None
        self._hass = hass

    def fetch(self):
        _LOGGER.debug("Starting Senertec energy system connection.")
        language = self.config_entry.options.get(CONF_LANG, DEFAULT_LANG)
        b = lang[language]
        self.senertec_client = senertec(
            self.supportedItems,
            self.config_entry.data[CONF_EMAIL],
            self.config_entry.data[CONF_PASSWORD],
            b,
        )
        self.senertec_client.messagecallback = self.ws_callback
        try:
            loginres = self.senertec_client.login()
            initres = self.senertec_client.init()
            if not loginres or not initres:
                _LOGGER.error("Init failed")
            units = self.senertec_client.getUnits()
            if units:
                if not self.senertec_client.connectUnit(units[0].serial):
                    return
                errors = self.senertec_client.getErrors()
                subErrorData = []
                if len(errors) == 0:
                    c = canipError()
                    c.code = "None"
                    c.currentError = True
                    subErrorData.append(c)
                    self.data.append(subErrorData)
                else:
                    self.data.append(errors)
                self._poll()
            else:
                _LOGGER.error("No units found")
        except Exception as ex:
            _LOGGER.error(ex)

    async def async_setup(self) -> None:
        """Set up senertec."""
        self.data = []

        async def request_update(call: ServiceCall) -> None:
            """Request update."""
            await self.async_request_refresh()

        self.hass.services.async_register(DOMAIN, SENERTEC_POLL_SERVICE, request_update)

    async def async_update(self):
        """Update senertec data."""
        _LOGGER.debug("Starting data update..")
        self.data = []
        self.subData = []
        await self.hass.async_add_executor_job(self.fetch)
        await self.stop()
        _LOGGER.debug("Finished data update.")
        return self.data

    def _poll(self):
        # clear old data
        _LOGGER.debug("Polling senertec sensors..")
        try:
            for points in self.senertec_client.boards:
                ids = points.getFullDataPointIds()
                self.senertec_client.request(ids)
            time.sleep(5)
            self.data.append(self.subData)
        except Exception as ex:
            _LOGGER.error(ex)

    async def stop(self):
        _LOGGER.debug("Stopping Senertec energy system connection.")
        await self.hass.async_add_executor_job(self.senertec_client.logout)

    def ws_callback(self, value: canipValue):
        _LOGGER.debug("Received senertec sensor value.")
        self.subData.append(value)
