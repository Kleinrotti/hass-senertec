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
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.typing import StateType
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import slugify
from senertec.client import canipError, canipValue, energyUnit

from . import SenertecCoordinator
from .const import DOMAIN, SENERTEC_COORDINATOR, SENERTEC_URL

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, config_entry: ConfigEntry, async_add_entities
):
    coordinator = hass.data[DOMAIN][SENERTEC_COORDINATOR]
    if coordinator.data:
        for value in coordinator.data.values():
            device = value.get("device")
            sensors = value.get("sensors", {})
            for sensor_value in sensors.values():
                async_add_entities([SenertecSensor(coordinator, sensor_value, device)])
            errors = value.get("errors", [])
            async_add_entities([SenertecErrorSensor(coordinator, errors, device)])
    else:
        _LOGGER.warning("No sensor data found")


class SenertecSensor(CoordinatorEntity, SensorEntity):
    """Representation of a senertec sensor."""

    coordinator: SenertecCoordinator

    def __init__(self, coordinator, value: canipValue, device: energyUnit):
        """Initialize the senertec sensor."""
        super().__init__(coordinator)
        self.device = device
        self._datapoint = value.sourceDatapoint
        # create a unique id from device serial + boardname which is the sensor connected to + the sensor datapoint id
        uid = "sensor." + slugify(f"{self.device.serial}_{value.sourceDatapoint}")
        self.entity_id = uid
        self._attr_unique_id = uid
        self._value: StateType = None
        self._unit = None
        self._name = None

    @property
    def name(self):
        entity = self.coordinator.data[self.device.serial]["sensors"].get(
            self._datapoint, None
        )
        if entity is not None:
            self._name = entity.friendlyDataName
        return self._name

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data:
            value = self.coordinator.data[self.device.serial]["sensors"].get(
                self._datapoint, None
            )
            if value is None:
                _LOGGER.debug(self.name + " (" + self._datapoint + ") was NoneType")
            self._value = cast(StateType, value.dataValue)
        return self._value

    @property
    def native_unit_of_measurement(self):
        if self.coordinator.data:
            value = self.coordinator.data[self.device.serial]["sensors"].get(
                self._datapoint, None
            )
            if value.dataUnit != "":
                self._unit = value.dataUnit
        return self._unit

    @property
    def device_class(self):
        unit = self.native_unit_of_measurement
        if unit == "W":
            return SensorDeviceClass.POWER
        if unit in ("Wh", "kWh"):
            return SensorDeviceClass.ENERGY
        if unit == "°C":
            return SensorDeviceClass.TEMPERATURE
        if unit == "%":
            return SensorDeviceClass.POWER_FACTOR
        if unit == "l":
            return SensorDeviceClass.VOLUME_STORAGE
        if unit == "m":
            return SensorDeviceClass.DISTANCE
        return None

    @property
    def state_class(self):
        unit = self.native_unit_of_measurement
        if unit in ("W", "Rpm"):
            return SensorStateClass.MEASUREMENT
        if unit in ("Wh", "kWh", "Hours"):
            return SensorStateClass.TOTAL_INCREASING
        return None

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device.serial)
            },
            name=f"{self.device.model} - {self.device.serial}",
            manufacturer="Senertec",
            model=self.device.model,
            serial_number=self.device.serial,
            configuration_url=SENERTEC_URL,
        )


class SenertecErrorSensor(CoordinatorEntity, SensorEntity):
    """Representation of a senertec error sensor."""

    coordinator: SenertecCoordinator

    def __init__(self, coordinator, value: list[canipError], device: energyUnit):
        """Initialize the senertec sensor."""
        super().__init__(coordinator)
        self.device = device
        uid = "sensor." + slugify(f"{device.serial} errors")
        self.entity_id = uid
        self._attr_unique_id = uid
        self._value: StateType = None

    @property
    def name(self):
        return "Current Errors"

    @property
    def native_value(self) -> StateType:
        if self.coordinator.data:
            merged = ""
            # merge all error codes to one value/string
            for error in self.coordinator.data[self.device.serial]["errors"]:
                merged += f"{error.code},"
            self._value = merged.removesuffix(",")
        return self._value

    @property
    def icon(self):
        return "mdi:alert"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return the state attributes."""
        if self.coordinator.data:
            translation = ""
            category = ""
            timestamp = ""
            board = ""
            for error in self.coordinator.data[self.device.serial]["errors"]:
                translation += f"{error.code}: {error.errorTranslation}\n"
                category += f"{error.code}: {error.errorCategory}\n"
                timestamp += (
                    f"{error.code}: {error.timestamp.strftime('%Y-%m-%d %H:%M:%S')}\n"
                )
                board += f"{error.code}: {error.boardName}\n"
            return {
                "translation": translation,
                "category": category,
                "timestamp": timestamp,
                "board": board,
            }
        return None

    @property
    def entity_category(self):
        return EntityCategory.DIAGNOSTIC

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.device.serial)
            },
            name=f"{self.device.model} - {self.device.serial}",
            manufacturer="Senertec",
            model=self.device.model,
            serial_number=self.device.serial,
            configuration_url=SENERTEC_URL,
        )
