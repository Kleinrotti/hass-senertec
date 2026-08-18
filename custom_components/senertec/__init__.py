"""The Senertec energy systems integration integration."""

from __future__ import annotations

import json
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    DOMAIN,
    PLATFORMS,
    PRODUCTGROUPS_OVERRIDE_FILENAME,
    PRODUCTGROUPSPATH,
    SENERTEC_COORDINATOR,
)
from .SenertecCoordinator import SenertecCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Senertec integration."""

    if DOMAIN not in hass.data:
        hass.data[DOMAIN] = {}
    return True


def _loadProductGroupsOverride(path: str) -> dict | None:
    if not os.path.isfile(path):
        return None
    try:
        with open(path, encoding="utf-8") as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError) as ex:
        _LOGGER.warning("Failed to load productGroups override at %s: %s", path, ex)
        return None


async def _getProductGroups(hass: HomeAssistant):
    file = await hass.async_add_executor_job(
        open,
        PRODUCTGROUPSPATH,
    )
    supportedItems = json.load(file)
    file.close()

    override_path = hass.config.path(DOMAIN, PRODUCTGROUPS_OVERRIDE_FILENAME)
    override = await hass.async_add_executor_job(
        _loadProductGroupsOverride, override_path
    )
    if override:
        supportedItems.update(override)
        _LOGGER.info(
            "Loaded productGroups override from %s, overriding groups: %s",
            override_path,
            list(override.keys()),
        )
    return supportedItems


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Senertec energy systems integration from a config entry."""
    _LOGGER.debug("Setting up senertec component")

    supportedItems = await _getProductGroups(hass)
    senertec_coordinator = SenertecCoordinator(
        hass,
        entry,
        supportedItems,
    )
    await senertec_coordinator.async_setup()
    await senertec_coordinator.async_refresh()
    hass.data[DOMAIN][SENERTEC_COORDINATOR] = senertec_coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True
