"""Support for senertec sensors."""
import logging

from typing import Any, cast
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.typing import StateType
from . import SenertecEnergySystemCoordinator
from senertec.client import canipValue, canipError
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, SENERTEC_COORDINATOR, SENERTEC_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    coordinator = hass.data[DOMAIN][SENERTEC_COORDINATOR]
    if coordinator.data:
        for lists in coordinator.data:
            if isinstance(lists[0], canipError):
                async_add_entities(
                    SenertecErrorSensor(coordinator, item) for item in lists
                )
            else:
                async_add_entities(SenertecSensor(coordinator, item) for item in lists)
    else:
        _LOGGER.warning("No sensor data found.")


class SenertecSensor(CoordinatorEntity, SensorEntity):
    """Representation of a senertec sensor."""

    coordinator: SenertecEnergySystemCoordinator

    def __init__(self, coordinator, value: canipValue):
        """Initialize the senertec sensor."""
        super().__init__(coordinator)
        self._device_serial = self.coordinator.config_entry.data["serial"]
        self._attr_name = f"{self._device_serial} {value.friendlyDataName}"
        self._attr_unique_id = value.sourceDatapoint
        self._value: StateType = None
        self._model = self.coordinator.config_entry.data["model"]
        self._unit = None

    @property
    def native_value(self) -> StateType:
        """Return native value for entity."""
        if self.coordinator.data:
            temp = next(
                (
                    x
                    for x in self.coordinator.data[1]
                    if x.sourceDatapoint == self._attr_unique_id
                ),
                None,
            )
            if temp == None:
                _LOGGER.warning(
                    self._attr_name + " (" + self._attr_unique_id + ") was NoneType"
                )
            else:
                if temp.dataUnit != "°C":
                    self._value = cast(StateType, temp.dataValue)
                else:
                    # filter out wrong measurements
                    if temp.dataValue > -50 and temp.dataValue < 250:
                        self._value = cast(StateType, temp.dataValue)
            return self._value

    @property
    def native_unit_of_measurement(self):
        if self.coordinator.data:
            temp = next(
                (
                    x
                    for x in self.coordinator.data[1]
                    if x.sourceDatapoint == self._attr_unique_id
                ),
                None,
            )
            self._unit = temp.dataUnit
        if self._unit != "":
            return self._unit

    @property
    def device_class(self):
        unit = self.native_unit_of_measurement
        if unit == "W":
            return SensorDeviceClass.POWER
        elif unit == "Wh" or unit == "kWh":
            return SensorDeviceClass.ENERGY
        elif unit == "°C":
            return SensorDeviceClass.TEMPERATURE
        elif unit == "%":
            return SensorDeviceClass.POWER_FACTOR
        elif unit == "l":
            return SensorDeviceClass.VOLUME_STORAGE
        elif unit == "m":
            return SensorDeviceClass.DISTANCE

    @property
    def state_class(self):
        unit = self.native_unit_of_measurement
        if unit == "W" or unit == "Rpm":
            return SensorStateClass.MEASUREMENT
        elif unit == "Wh" or unit == "kWh" or unit == "Hours":
            return SensorStateClass.TOTAL_INCREASING

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._device_serial)
            },
            "name": self._device_serial,
            "manufacturer": "Senertec",
            "model": self._model,
            "configuration_url": SENERTEC_URL,
        }


class SenertecErrorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a senertec sensor."""

    coordinator: SenertecEnergySystemCoordinator

    def __init__(self, coordinator, value: canipError):
        """Initialize the senertec sensor."""
        super().__init__(coordinator)
        self._device_serial = self.coordinator.config_entry.data["serial"]
        self._attr_name = f"{self._device_serial} Errors"
        self._attr_unique_id = "errors"
        self._value: StateType = None
        self._model = self.coordinator.config_entry.data["model"]

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data:
            self._value = self.coordinator.data[0][0]
        return self._value.code

    @property
    def icon(self):
        return "mdi:alert"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data:
            data = self.coordinator.data[0][0]
            return {
                "translation": data.errorTranslation,
                "category": data.errorCategory,
                "timestamp": data.timestamp,
                "board": data.boardName,
            }

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self):
        return {
            "identifiers": {
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self._device_serial)
            },
            "name": self._device_serial,
            "manufacturer": "Senertec",
            "model": self._model,
            "configuration_url": SENERTEC_URL,
        }
