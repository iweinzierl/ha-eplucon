import logging
import voluptuous as vol
from typing import Any, Dict, Optional
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.helpers import aiohttp_client
from homeassistant.data_entry_flow import FlowResult
from .const import DOMAIN, SUPPORTED_TYPES
from .eplucon_api.eplucon_client import EpluconApi, ApiAuthError, ApiError, BASE_URL

_LOGGER = logging.getLogger(__name__)

# Define the schema for the user input (API token)
DATA_SCHEMA = vol.Schema({
    vol.Required("api_token"): str,
    vol.Required("api_endpoint", default=BASE_URL): str
})


class EpluconConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Eplucon."""

    VERSION = 1

    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}

        _LOGGER.info("Starting Eplucon config flow")

        if user_input is not None:
            _LOGGER.debug("Processing user input for Eplucon config")
            # Attempt to connect to the API using the provided API token & endpoint
            api_token: str = user_input["api_token"]
            api_endpoint: str = user_input['api_endpoint']
            _LOGGER.debug(f"Attempting to connect to API endpoint: {api_endpoint}")
            
            client = EpluconApi(api_token, api_endpoint, aiohttp_client.async_get_clientsession(self.hass))

            try:
                _LOGGER.debug("Fetching devices from Eplucon API")
                devices = await client.get_devices()

                _LOGGER.info(f"Received {len(devices)} devices from API: {[f'{d.name} (ID: {d.id})' for d in devices]}")

                supported_devices = []
                for device in devices:
                    if device.type not in SUPPORTED_TYPES:
                        _LOGGER.warning(
                            f"Device {device.name} (ID: {device.id}) with type {device.type} is not supported yet. Skipping...")
                    else:
                        supported_devices.append(device)
                        _LOGGER.debug(f"Device {device.name} (ID: {device.id}) with type {device.type} is supported")

                if len(supported_devices) > 0:
                    _LOGGER.info(f"Creating config entry with {len(supported_devices)} supported devices")
                    return self.async_create_entry(title="Eplucon", data={"devices": supported_devices, "api_token": api_token, "api_endpoint": api_endpoint})

                _LOGGER.warning("No supported devices found")
                errors["base"] = "no-devices"

            except ApiAuthError as e:
                # Handle authentication error
                _LOGGER.error(f"Authentication failed with the provided API token: {e}")
                errors["base"] = "auth"

            except ApiError as e:
                # Handle general API error
                _LOGGER.error(f"Failed to fetch devices from Eplucon API: {e}")
                errors["base"] = "api"

            except Exception as e:
                # Handle any other unexpected exceptions
                _LOGGER.exception("Unexpected exception during config flow: %s", e)
                errors["base"] = "unknown"

        # If the user input is not valid or an error occurred, show the form again with the error message
        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Get the options flow for this handler."""
        return EpluconOptionsFlowHandler(config_entry)


class EpluconOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle Eplucon options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize Eplucon options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None) -> FlowResult:
        """Manage the options for the integration."""
        errors: Dict[str, str] = {}
        
        _LOGGER.info("Starting Eplucon options flow")

        if user_input is not None:
            _LOGGER.debug("Processing user input for Eplucon options")
            # If the user has provided new data, update the config entry
            api_token = user_input.get("api_token")
            api_endpoint = user_input.get("api_endpoint")
            
            _LOGGER.debug(f"Validating new API credentials for endpoint: {api_endpoint}")

            # Revalidate the API token to ensure it's correct
            client = EpluconApi(api_token, api_endpoint, aiohttp_client.async_get_clientsession(self.hass))

            try:
                _LOGGER.debug("Fetching devices to validate credentials")
                devices = await client.get_devices()

                _LOGGER.info(f"Found {len(devices)} devices during options validation")

                # Skip unsupported devices
                supported_devices = []
                for device in devices:
                    if device.type not in SUPPORTED_TYPES:
                        _LOGGER.warning(
                            f"Device {device.name} (ID: {device.id}) with type {device.type} is not supported yet. Skipping...")
                    else:
                        supported_devices.append(device)

                if len(supported_devices) > 0:
                    _LOGGER.info(f"Updating config entry with {len(supported_devices)} supported devices")
                    # Update the configuration entry with the new API token and devices
                    self.hass.config_entries.async_update_entry(
                        self.config_entry,
                        data={
                            "api_token": api_token,
                            "api_endpoint": api_endpoint,
                            "devices": supported_devices
                        }
                    )
                    _LOGGER.info("Config entry updated successfully")
                    return self.async_create_entry(title="", data={})

                _LOGGER.warning("No supported devices found during options validation")
                errors["base"] = "no-devices"

            except ApiAuthError as e:
                # Handle authentication error
                _LOGGER.error(f"Authentication failed during options validation: {e}")
                errors["base"] = "auth"

            except ApiError as e:
                # Handle general API error
                _LOGGER.error(f"API error during options validation: {e}")
                errors["base"] = "api"

            except Exception as e:
                # Handle any other unexpected exceptions
                _LOGGER.exception("Unexpected exception during options flow: %s", e)
                errors["base"] = "unknown"

        # Show the options form with the current API token as the default value
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Required("api_token", default=self.config_entry.data.get("api_token")): str,
                vol.Required("api_endpoint", default=self.config_entry.data.get("api_endpoint", BASE_URL)): str
            }),
            errors=errors
        )

