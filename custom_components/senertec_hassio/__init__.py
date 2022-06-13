"""The Senertec energy systems integration integration."""
from __future__ import annotations
import json
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .SenertecEnergySystemCoordinator import SenertecEnergySystemCoordinator

from .const import (
    PLATFORMS,
    DOMAIN,
    SENERTEC_COORDINATOR,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Gardena Smart System integration."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


async def _getProductGroups(hass: HomeAssistant):
    file = await hass.async_add_executor_job(
        open,
        "/config/custom_components/senertec_hassio/productGroups.json",
    )
    supportedItems = json.load(file)
    file.close()
    return supportedItems


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Senertec energy systems integration from a config entry."""
    _LOGGER.debug("Setting up senertec component")

    supportedItems = await _getProductGroups(hass)
    senertec_coordinator = SenertecEnergySystemCoordinator(
        hass,
        entry,
        supportedItems,
    )
    await senertec_coordinator.async_setup()
    await senertec_coordinator.async_refresh()
    hass.data[DOMAIN][SENERTEC_COORDINATOR] = senertec_coordinator
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    return True
