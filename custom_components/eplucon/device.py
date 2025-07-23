from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from .const import DOMAIN, MANUFACTURER

import logging

from .eplucon_api.DTO.DeviceDTO import DeviceDTO

_LOGGER = logging.getLogger(__name__)


class EpluconDevice:
    def __init__(
            self,
            hass: HomeAssistant,
            entry: ConfigEntry,
            device: DeviceDTO,
    ) -> None:
        _LOGGER.info(
            f"Initializing EpluconDevice: {device.name} with ID '{device.id}', type '{device.type}'"
        )
        self.device_registry = dr.async_get(hass)
        
        device_identifiers = (DOMAIN, f"Eplucon {device.id}")
        _LOGGER.debug(f"Creating device with identifiers: {device_identifiers}")
        
        self.device = self.device_registry.async_get_or_create(
            config_entry_id=entry.entry_id,
            name=f"Eplucon {device.name}",
            model=f"{device.type}",
            manufacturer=MANUFACTURER,
            identifiers={device_identifiers}
        )
        
        _LOGGER.info(f"Successfully created/retrieved device: {self.device.name} (registry ID: {self.device.id})")
        _LOGGER.debug(f"Device details - Name: {self.device.name}, Model: {self.device.model}, Manufacturer: {self.device.manufacturer}")
