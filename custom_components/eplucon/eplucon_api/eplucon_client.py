from __future__ import annotations

import aiohttp
import logging
from typing import Any, Optional

from .DTO.CommonInfoDTO import CommonInfoDTO
from .DTO.DeviceDTO import DeviceDTO
from .DTO.RealtimeInfoDTO import RealtimeInfoDTO
from .DTO.HeatLoadingDTO import HeatLoadingDTO

BASE_URL = "https://portaal.eplucon.nl/api/v2"
_LOGGER: logging.Logger = logging.getLogger(__package__)


class ApiAuthError(Exception):
    pass


class ApiError(Exception):
    pass


class EpluconApi:
    """Client to talk to Eplucon API"""

    def __init__(self, api_token: str, api_endpoint: str|None, session: Optional[aiohttp.ClientSession] = None) -> None:
        self._base = api_endpoint if api_endpoint else BASE_URL
        self._session = session or aiohttp.ClientSession()
        self._headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Authorization": f"Bearer {api_token}"
        }

        _LOGGER.debug("Initialize Eplucon API client")
        _LOGGER.debug(f"API endpoint: {self._base}")
        _LOGGER.debug(f"Headers configured: {self._sanitize_headers_for_logging(self._headers)}")

    def _sanitize_headers_for_logging(self, headers: dict) -> dict:
        """Sanitize headers for logging by masking sensitive information."""
        sanitized = headers.copy()
        if 'Authorization' in sanitized:
            auth_value = sanitized['Authorization']
            if auth_value.startswith('Bearer '):
                token = auth_value[7:]  # Remove 'Bearer ' prefix
                masked_token = token[:8] + '*' * (len(token) - 12) + token[-4:] if len(token) > 12 else '*' * len(token)
                sanitized['Authorization'] = f'Bearer {masked_token}'
        return sanitized

    async def get_devices(self) -> list[DeviceDTO]:
        url = f"{self._base}/econtrol/modules"
        _LOGGER.debug(f"Eplucon Get devices {url}")
        _LOGGER.debug(f"Request headers: {self._sanitize_headers_for_logging(self._headers)}")
        try:
            async with self._session.get(url, headers=self._headers) as response:
                _LOGGER.debug(f"API response status: {response.status} for get_devices")
                _LOGGER.debug(f"Response headers: {dict(response.headers)}")
                if response.status != 200:
                    _LOGGER.error(f"API returned non-200 status: {response.status} for get_devices")
                    raise ApiError(f"API returned status {response.status}")
                
                devices = await response.json()
                _LOGGER.debug(f"Raw devices response: {devices}")
                self.validate_response(devices)
                data = devices.get('data', [])
                _LOGGER.info(f"Successfully retrieved {len(data)} devices from API")
                device_dtos = [DeviceDTO(**device) for device in data]
                _LOGGER.debug(f"Created DeviceDTO objects: {[f'Device {d.id}: {d.name}' for d in device_dtos]}")
                return device_dtos
        except Exception as e:
            _LOGGER.error(f"Error in get_devices: {type(e).__name__}: {e}")
            raise

    async def get_realtime_info(self, module_id: int) -> RealtimeInfoDTO:
        url = f"{self._base}/econtrol/modules/{module_id}/get_realtime_info"
        _LOGGER.debug(f"Eplucon Get realtime info for {module_id}: {url}")
        _LOGGER.debug(f"Request headers: {self._sanitize_headers_for_logging(self._headers)}")

        try:
            async with self._session.get(url, headers=self._headers) as response:
                _LOGGER.debug(f"API response status: {response.status} for get_realtime_info module {module_id}")
                _LOGGER.debug(f"Response headers: {dict(response.headers)}")
                if response.status != 200:
                    _LOGGER.error(f"API returned non-200 status: {response.status} for get_realtime_info module {module_id}")
                    raise ApiError(f"API returned status {response.status}")
                
                data = await response.json()
                _LOGGER.debug(f"Raw realtime info response for module {module_id}: {data}")
                self.validate_response(data)
                
                # Create a completely fresh object from the API data
                # This ensures we don't have any old data lingering
                common_info = CommonInfoDTO(**data['data']['common'])
                _LOGGER.debug(f"Created CommonInfoDTO for module {module_id}: indoor_temp={common_info.indoor_temperature}, outdoor_temp={common_info.outdoor_temperature}")
                heatpump_info = data['data']['heatpump']  # Not sure what this could be
                _LOGGER.debug(f"Heatpump info for module {module_id}: {heatpump_info}")
                
                # Create a new DTO with the fresh data
                realtime_info = RealtimeInfoDTO(common=common_info, heatpump=heatpump_info)

                # Add debug info to compare with any previous values
                # This will help diagnose if values are being updated correctly
                _LOGGER.debug(f"Module {module_id} realtime data - " + 
                             f"brine_in_temp: {common_info.brine_in_temperature}, " +
                             f"brine_out_temp: {common_info.brine_out_temperature}, " +
                             f"indoor_temp: {common_info.indoor_temperature}, " +
                             f"outdoor_temp: {common_info.outdoor_temperature}")
                
                _LOGGER.info(f"Successfully retrieved realtime info for module {module_id}")
                return realtime_info
        except Exception as e:
            _LOGGER.error(f"Error in get_realtime_info for module {module_id}: {type(e).__name__}: {e}")
            raise

    async def get_heatpump_heatloading_status(self, module_id: int) -> dict:
        url = f"{self._base}/econtrol/modules/{module_id}/heatloading_status"
        _LOGGER.debug(f"Eplucon Get heatpump heatloading status for {module_id}: {url}")
        _LOGGER.debug(f"Request headers: {self._sanitize_headers_for_logging(self._headers)}")

        try:
            async with self._session.get(url, headers=self._headers) as response:
                _LOGGER.debug(f"API response status: {response.status} for get_heatpump_heatloading_status module {module_id}")
                _LOGGER.debug(f"Response headers: {dict(response.headers)}")
                if response.status != 200:
                    _LOGGER.error(f"API returned non-200 status: {response.status} for get_heatpump_heatloading_status module {module_id}")
                    raise ApiError(f"API returned status {response.status}")
                
                data = await response.json()
                _LOGGER.debug(f"Raw heatloading status response for module {module_id}: {data}")
                self.validate_response(data)

                heatloading_status = HeatLoadingDTO(**data['data'])
                _LOGGER.debug(f"Created HeatLoadingDTO for module {module_id}: active={heatloading_status.heatloading_active}, configurations={heatloading_status.configurations}")
                _LOGGER.info(f"Successfully retrieved heatloading status for module {module_id}")
                return heatloading_status
        except Exception as e:
            _LOGGER.error(f"Error in get_heatpump_heatloading_status for module {module_id}: {type(e).__name__}: {e}")
            raise

    @staticmethod
    def validate_response(response: Any) -> None:
        _LOGGER.debug(f"Validating API response structure: has 'auth' key: {'auth' in response}")
        if 'auth' not in response:
            _LOGGER.error("Error from Eplucon API, expecting auth key in response.")
            raise ApiError('Error from Eplucon API, expecting auth key in response.')

        auth_status = response['auth']
        _LOGGER.debug(f"API auth status: {auth_status}")
        if not auth_status:
            _LOGGER.error("Authentication failed: Please check the given API key.")
            raise ApiAuthError("Authentication failed: Please check the given API key.")
        
        _LOGGER.debug("API response validation successful")
