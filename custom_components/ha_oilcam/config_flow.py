"""Config flow for the Oilcam integration."""

import logging

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    CONF_CAPACITY,
    CONF_COLOR_BOX,
    CONF_COLOR_FULL,
    CONF_COLOR_LOW,
    CONF_COLOR_MEDIUM,
    CONF_HOST,
    CONF_LEVEL_LOW,
    CONF_LEVEL_MEDIUM,
    CONF_PORT,
    CONF_REGION,
    CONF_THRESHOLD_MAX,
    CONF_THRESHOLD_MIN,
    CONF_UPDATE_CYCLE,
    CONF_URL,
    CONF_ZIPCODE,
    DOMAIN,
)

_LOGGER = logging.getLogger(__name__)

CONFIG_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default="192.168.80.16"): str,
        vol.Required(CONF_PORT, default=8000): cv.port,
        vol.Required(
            CONF_URL, default="http://thingino:thingino@192.168.42.4/image.jpg"
        ): str,
        vol.Required(CONF_UPDATE_CYCLE, default=300): cv.positive_int,
        vol.Required(CONF_ZIPCODE, default="97222"): str,
        vol.Required(CONF_REGION, default="880,130,910,1070"): str,
        vol.Required(CONF_THRESHOLD_MIN, default=140): cv.positive_int,
        vol.Required(CONF_THRESHOLD_MAX, default=255): cv.positive_int,
        vol.Required(CONF_CAPACITY, default=2400): cv.positive_int,
        vol.Required(CONF_LEVEL_LOW, default=10): cv.positive_int,
        vol.Required(CONF_LEVEL_MEDIUM, default=50): cv.positive_int,
        vol.Required(CONF_COLOR_LOW, default="#FF0000"): str,
        vol.Required(CONF_COLOR_MEDIUM, default="#FFFF00"): str,
        vol.Required(CONF_COLOR_FULL, default="#00FF00"): str,
        vol.Required(CONF_COLOR_BOX, default="#0000FF"): str,
    }
)


class OilcamConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Oilcam."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Handle the initial configuration step."""
        errors = {}
        if user_input is not None:
            try:
                return self.async_create_entry(title="Oilcam", data=user_input)
            except Exception:
                errors["base"] = "unknown"
                _LOGGER.exception("Unexpected error during setup")

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> config_entries.OptionsFlow:
        """Return the options flow handler."""
        return OilcamOptionsFlow(config_entry)


class OilcamOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Oilcam."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize the options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict | None = None
    ) -> config_entries.FlowResult:
        """Manage the options configuration."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Use the same schema as initial setup, pre-filled with current values
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_HOST,
                        default=self.config_entry.data.get(CONF_HOST, "192.168.80.16"),
                    ): str,
                    vol.Required(
                        CONF_PORT,
                        default=self.config_entry.data.get(CONF_PORT, 8000),
                    ): cv.port,
                    vol.Required(
                        CONF_URL,
                        default=self.config_entry.data.get(
                            CONF_URL, "http://thingino:thingino@192.168.42.4/image.jpg"
                        ),
                    ): str,
                    vol.Required(
                        CONF_UPDATE_CYCLE,
                        default=self.config_entry.data.get(CONF_UPDATE_CYCLE, 300),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_ZIPCODE,
                        default=self.config_entry.data.get(CONF_ZIPCODE, "97222"),
                    ): str,
                    vol.Required(
                        CONF_REGION,
                        default=self.config_entry.data.get(
                            CONF_REGION, "880,130,910,1070"
                        ),
                    ): str,
                    vol.Required(
                        CONF_THRESHOLD_MIN,
                        default=self.config_entry.data.get(CONF_THRESHOLD_MIN, 140),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_THRESHOLD_MAX,
                        default=self.config_entry.data.get(CONF_THRESHOLD_MAX, 255),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_CAPACITY,
                        default=self.config_entry.data.get(CONF_CAPACITY, 2400),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_LEVEL_LOW,
                        default=self.config_entry.data.get(CONF_LEVEL_LOW, 10),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_LEVEL_MEDIUM,
                        default=self.config_entry.data.get(CONF_LEVEL_MEDIUM, 50),
                    ): cv.positive_int,
                    vol.Required(
                        CONF_COLOR_LOW,
                        default=self.config_entry.data.get(CONF_COLOR_LOW, "#FF0000"),
                    ): str,
                    vol.Required(
                        CONF_COLOR_MEDIUM,
                        default=self.config_entry.data.get(
                            CONF_COLOR_MEDIUM, "#FFFF00"
                        ),
                    ): str,
                    vol.Required(
                        CONF_COLOR_FULL,
                        default=self.config_entry.data.get(CONF_COLOR_FULL, "#00FF00"),
                    ): str,
                    vol.Required(
                        CONF_COLOR_BOX,
                        default=self.config_entry.data.get(CONF_COLOR_BOX, "#0000FF"),
                    ): str,
                }
            ),
        )
