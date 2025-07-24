import logging
from datetime import timedelta
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers import device_registry
from .eplucon_api.eplucon_client import EpluconApi, ApiError, DeviceDTO, BASE_URL
from .const import DOMAIN, PLATFORMS, EPLUCON_PORTAL_URL, MANUFACTURER, SUPPORTED_TYPES
from dacite import from_dict

_LOGGER = logging.getLogger(__name__)

# Time between data updates
UPDATE_INTERVAL = timedelta(seconds=30)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Eplucon from a config entry."""
    _LOGGER.info(f"Setting up Eplucon integration with entry ID: {entry.entry_id}")
    
    api_token = entry.data["api_token"]
    api_endpoint = entry.data.get("api_endpoint", BASE_URL)
    _LOGGER.debug(f"Using API endpoint: {api_endpoint}")

    devices = entry.data["devices"]
    _LOGGER.info(f"Found {len(devices)} devices in config entry")

    session = async_get_clientsession(hass)
    client = EpluconApi(api_token, api_endpoint, session)

    _LOGGER.debug("Registering devices in Home Assistant device registry")
    await register_devices(devices, entry, hass)

    async def async_update_data() -> list[DeviceDTO]:
        """Fetch Eplucon data from API endpoint."""
        _LOGGER.debug("Starting coordinator data update cycle")
        start_time = __import__('time').time()
        
        try:
            # Make a completely fresh copy of the devices to avoid any data sharing issues
            entry_devices = []
            for device in entry.data["devices"]:
                if isinstance(device, dict):
                    # Create a deep copy of the device dictionary
                    device_copy = {key: value for key, value in device.items()}
                    entry_devices.append(device_copy)
                else:
                    # Create a new DTO object from scratch to avoid any reference issues
                    device_dict = {key: value for key, value in device.__dict__.items() 
                                  if not key.startswith('_') and key != 'realtime_info' and key != 'heatloading_status'}
                    entry_devices.append(device_dict)
            
            _LOGGER.info(f"Fetching data from Eplucon API for {len(entry_devices)} devices")

            # Track which devices we should include in the final result
            final_devices = []
            
            # For each device, fetch the real-time info and combine it with the device data
            for i, entry_device in enumerate(entry_devices):
                _LOGGER.debug(f"Processing device {i+1}/{len(entry_devices)}: {entry_device}")
                entry_device = await device_dict_to_dto(entry_device)

                _LOGGER.debug(f"Converted to DTO - Device ID: {entry_device.id}, Name: {entry_device.name}, Type: {entry_device.type}")

                # Skip unsupported devices
                if entry_device.type not in SUPPORTED_TYPES:
                    _LOGGER.warning(f"Device {entry_device.name} (ID: {entry_device.id}) with type {entry_device.type} is not supported yet. Skipping...")
                    continue

                # Now make API calls to get the latest data
                _LOGGER.debug(f"Fetching realtime info for device {entry_device.id}")
                realtime_info = await client.get_realtime_info(entry_device.id)
                
                # Create a completely new device DTO to ensure we're not reusing any objects
                new_device = DeviceDTO(
                    id=entry_device.id,
                    name=entry_device.name,
                    type=entry_device.type,
                    account_module_index=entry_device.account_module_index,
                    realtime_info=realtime_info  # Assign the new realtime info
                )

                _LOGGER.debug(f"Fetching heatloading status for device {new_device.id}")
                heatloading_status = await client.get_heatpump_heatloading_status(new_device.id)
                new_device.heatloading_status = heatloading_status
                
                # Log some key data points to verify it's being updated
                if new_device.realtime_info and new_device.realtime_info.common:
                    _LOGGER.debug(f"New device data: brine_out_temp={new_device.realtime_info.common.brine_out_temperature}, " + 
                                 f"indoor_temp={new_device.realtime_info.common.indoor_temperature}")
                
                # Add the new device to our result list
                final_devices.append(new_device)
                _LOGGER.info(f"Successfully updated data for device {new_device.name} (ID: {new_device.id})")

            elapsed_time = __import__('time').time() - start_time
            _LOGGER.info(f"Data update cycle completed successfully for {len(final_devices)} devices")
            _LOGGER.debug(f"Finished fetching Eplucon devices data in {elapsed_time:.3f} seconds (success: True)")
            return final_devices

        except ApiError as err:
            _LOGGER.error(f"Error fetching data from Eplucon API: {err}")
            raise err

        except Exception as err:
            _LOGGER.error(f"Unexpected error during data update: {type(err).__name__}: {err}", exc_info=True)
            raise err

    # Set up the coordinator to manage fetching data from the API
    _LOGGER.debug(f"Setting up DataUpdateCoordinator with {UPDATE_INTERVAL.total_seconds()}s update interval")
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="Eplucon devices",
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    # Fetch initial data so we have data when entities subscribe
    _LOGGER.debug("Performing initial coordinator refresh")
    await coordinator.async_config_entry_first_refresh()
    _LOGGER.info("Initial coordinator refresh completed successfully")

    # Store the coordinator in hass.data, so it's accessible in other parts of the integration
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator

    # Forward the setup to the sensor platform
    _LOGGER.debug(f"Forwarding setup to platforms: {PLATFORMS}")
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    _LOGGER.info("Eplucon integration setup completed successfully")
    return True


async def register_devices(devices, entry, hass):
    """Register devices in Home Assistant device registry."""
    _LOGGER.debug(f"Registering {len(devices)} devices in Home Assistant device registry")
    hass_device_registry = device_registry.async_get(hass)
    
    for i, device in enumerate(devices):
        device = await device_dict_to_dto(device)
        _LOGGER.debug(f"Registering device {i+1}/{len(devices)}: {device.name} (ID: {device.id})")

        registered_device = hass_device_registry.async_get_or_create(
            configuration_url=EPLUCON_PORTAL_URL,
            config_entry_id=entry.entry_id,
            identifiers={(DOMAIN, device.account_module_index)},
            manufacturer=MANUFACTURER,
            suggested_area="Utility Room",
            name=device.name,
            model=device.type,
        )
        _LOGGER.debug(f"Device registered successfully: {registered_device.name} with identifiers {registered_device.identifiers}")
    
    _LOGGER.info(f"Successfully registered {len(devices)} devices in Home Assistant")


async def device_dict_to_dto(device_dict: DeviceDTO|dict) -> DeviceDTO:
    """
        When retrieving given devices from HASS config flow the entry.data["devices"]
        is type list[DeviceDTO] but on boot this is a list[dict], not sure why and if this is intended,
        but this method will ensure we can parse the correct format here.
    """
    if isinstance(device_dict, dict):
        _LOGGER.debug(f"Converting device dict to DTO: {device_dict}")
        device_dict = from_dict(data_class=DeviceDTO, data=device_dict)
        _LOGGER.debug(f"Converted to DeviceDTO: ID={device_dict.id}, Name={device_dict.name}")
    else:
        _LOGGER.debug(f"Device already a DTO: ID={device_dict.id}, Name={device_dict.name}")
    return device_dict


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.info(f"Unloading Eplucon integration entry: {entry.entry_id}")
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        _LOGGER.debug("Successfully unloaded platforms, removing coordinator from hass.data")
        hass.data[DOMAIN].pop(entry.entry_id)
        _LOGGER.info("Eplucon integration unloaded successfully")
    else:
        _LOGGER.error("Failed to unload Eplucon platforms")

    return unload_ok
