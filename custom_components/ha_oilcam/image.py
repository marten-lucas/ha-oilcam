"""Image platform for the Oilcam integration."""

import logging

import requests

from homeassistant.components.image import ImageEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    CONF_COLOR_BOX,
    CONF_COLOR_FULL,
    CONF_COLOR_LOW,
    CONF_COLOR_MEDIUM,
    CONF_LEVEL_LOW,
    CONF_LEVEL_MEDIUM,
    DOMAIN,
)
from .coordinator import OilcamDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Oilcam image entities."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    entities = [
        OilcamRawImage(hass, entry),
        OilcamAnnotatedImage(hass, coordinator, entry),
    ]
    async_add_entities(entities)


class OilcamRawImage(ImageEntity):
    """Representation of the raw Oilcam image."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the raw image entity."""
        super().__init__(hass)
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_raw_image"
        self._attr_name = "Oilcam Raw Image"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Oilcam",
            "manufacturer": "Custom",
        }

    async def async_image(self) -> bytes | None:
        """Return the raw image from the camera URL."""
        try:
            response = await self.hass.async_add_executor_job(
                requests.get, self._entry.data["url"]
            )
            response.raise_for_status()
        except requests.RequestException as err:
            _LOGGER.error("Failed to fetch raw image: %s", err)
            return None
        else:
            return response.content


class OilcamAnnotatedImage(ImageEntity):
    """Representation of the annotated Oilcam image."""

    def __init__(
        self,
        hass: HomeAssistant,
        coordinator: OilcamDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the annotated image entity."""
        super().__init__(hass)
        self.coordinator = coordinator
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_annotated_image"
        self._attr_name = "Oilcam Annotated Image"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, entry.entry_id)},
            "name": "Oilcam",
            "manufacturer": "Custom",
        }

    async def async_image(self) -> bytes | None:
        """Return the annotated image from the API."""
        try:
            api_url = f"http://{self._entry.data['host']}:{self._entry.data['port']}/filling-image/"
            params = {
                "image_url": self._entry.data["url"],
                "region": self._entry.data["region"],
                "threshold_min": self._entry.data["threshold_min"],
                "threshold_max": self._entry.data["threshold_max"],
                "levelLow": self._entry.data[CONF_LEVEL_LOW],
                "levelMedium": self._entry.data[CONF_LEVEL_MEDIUM],
                "colorLow": self._entry.data[CONF_COLOR_LOW],
                "colorMedium": self._entry.data[CONF_COLOR_MEDIUM],
                "colorFull": self._entry.data[CONF_COLOR_FULL],
                "colorBox": self._entry.data[CONF_COLOR_BOX],
            }
            response = await self.hass.async_add_executor_job(
                requests.get, api_url, params
            )
            response.raise_for_status()
        except requests.RequestException as err:
            _LOGGER.error("Failed to fetch annotated image: %s", err)
            return None
        else:
            return response.content
