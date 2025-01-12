"""Constants for the Senertec energy systems integration integration."""

from pathlib import Path
from typing import Final

import voluptuous as vol

from homeassistant.const import CONF_EMAIL, CONF_PASSWORD, CONF_SCAN_INTERVAL, Platform

DOMAIN = "senertec"
DEFAULT_POLL_INTERVAL: Final = 10
SENERTEC_COORDINATOR = "senertec_coordinator"
# SENERTEC_SENSORS = "senertec_sensors"
DEFAULT_LANG = "English"
LANGUAGES = ["German", "English"]
CONF_LANG: Final = "sensor_lang"
PLATFORMS: Final = [Platform.SENSOR]
SENERTEC_POLL_SERVICE: Final = "senertec"
# DEFAULT_NAME = "Senertec"
SENERTEC_URL = "https://dachsconnect.senertec.com"
PRODUCTGROUPSPATH = Path(Path(__file__).parent.resolve(), "productGroups.json")

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Optional(
            CONF_LANG,
            default=DEFAULT_LANG,
        ): vol.In(LANGUAGES),
        vol.Optional(
            CONF_SCAN_INTERVAL,
            default=DEFAULT_POLL_INTERVAL,
        ): int,
    }
)
