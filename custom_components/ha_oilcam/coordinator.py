"""Data update coordinator for the Oilcam integration."""

from datetime import timedelta
import logging

import requests

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class OilcamDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching Oilcam data from the API."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize the data coordinator."""
        self.entry = entry
        self.hass = hass
        update_interval = timedelta(seconds=entry.data["update_cycle"])
        _LOGGER.debug(
            "Initializing coordinator with update interval: %s seconds",
            entry.data["update_cycle"],
        )
        super().__init__(
            hass,
            _LOGGER,
            name="ha_oilcam",
            update_interval=update_interval,
        )

    async def _async_update_data(self) -> dict:
        """Fetch data from the Oilcam API."""

        try:
            api_url = f"http://{self.entry.data['host']}:{self.entry.data['port']}/filling-data/"
            params = {
                "image_url": self.entry.data["url"],
                "region": self.entry.data["region"],
                "threshold_min": self.entry.data["threshold_min"],
                "threshold_max": self.entry.data["threshold_max"],
                "capacity": self.entry.data["capacity"],
                "zipcode": self.entry.data["zipcode"],
            }
            _LOGGER.debug("Fetching data from %s with params: %s", api_url, params)
            response = await self.hass.async_add_executor_job(
                requests.get, api_url, params
            )
            response.raise_for_status()
            data = response.json()
            _LOGGER.debug("Successfully fetched data: %s", data)
        except requests.RequestException as err:
            _LOGGER.error("Error fetching data: %s", err)
            raise UpdateFailed(f"Error fetching data: {err}") from err
        else:
            return data
