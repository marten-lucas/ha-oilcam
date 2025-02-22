"""Sensor platform for the Oilcam integration."""

import logging

from homeassistant.components.sensor import SensorEntity, SensorEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import OilcamDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

SENSOR_DESCRIPTIONS = [
    SensorEntityDescription(
        key="filling_level",
        name="Filling Level",
        native_unit_of_measurement="%",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="filled_capacity",
        name="Filled Capacity",
        native_unit_of_measurement="L",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="empty_capacity",
        name="Empty Capacity",
        native_unit_of_measurement="L",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="oilprice",
        name="Oil Price",
        native_unit_of_measurement="€",
        state_class="measurement",
    ),
    SensorEntityDescription(
        key="refillprice",
        name="Refill Price",
        native_unit_of_measurement="€",
        state_class="measurement",
    ),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oilcam sensor entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [OilcamSensor(coordinator, entry, desc) for desc in SENSOR_DESCRIPTIONS]
    async_add_entities(entities)


class OilcamSensor(SensorEntity):
    """Representation of an Oilcam sensor entity."""

    def __init__(
        self,
        coordinator: OilcamDataUpdateCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        """Initialize the sensor."""
        self.coordinator = coordinator
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Oilcam",
            "manufacturer": "Custom",
        }
        _LOGGER.debug("Initialized sensor: %s", description.key)

    @property
    def available(self) -> bool:
        """Return if the sensor is available."""
        available = (
            self.coordinator.last_update_success and self.coordinator.data is not None
        )
        _LOGGER.debug(
            "Sensor %s availability: %s", self.entity_description.key, available
        )
        return available

    @property
    def native_value(self) -> str | float | None:
        """Return the native value of the sensor."""
        if not self.available:
            _LOGGER.debug(
                "Sensor %s unavailable, returning None", self.entity_description.key
            )
            return None
        value = self.coordinator.data.get(self.entity_description.key)
        _LOGGER.debug("Sensor %s value: %s", self.entity_description.key, value)
        return value

    @property
    def extra_state_attributes(self) -> dict[str, str] | None:
        """Return additional state attributes."""
        if self.entity_description.key in ["oilprice", "refillprice"]:
            currency = self.coordinator.data.get("currency", "€")
            _LOGGER.debug(
                "Sensor %s currency attribute: %s",
                self.entity_description.key,
                currency,
            )
            return {"currency": currency}
        return None
