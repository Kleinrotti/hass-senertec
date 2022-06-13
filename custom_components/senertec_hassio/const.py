"""Constants for the Senertec energy systems integration integration."""

from homeassistant.const import (
    Platform,
)
from typing import Final
import voluptuous as vol

DOMAIN = "senertec_hassio"
DEFAULT_POLL_INTERVAL: Final = 10
SENERTEC_COORDINATOR = "senertec_coordinator"
SENERTEC_SENSORS = "senertec_sensors"
DEFAULT_LANG = "English"
LANGUAGES = ["German", "English"]
CONF_LANG: Final = "sensor_lang"
PLATFORMS: Final = [Platform.SENSOR]
SENERTEC_POLL_SERVICE: Final = "senertec"
DEFAULT_NAME = "Senertec"
SENERTEC_URL = "https://dachsconnect.senertec.com"

from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)
