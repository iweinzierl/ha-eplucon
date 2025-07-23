#!/usr/bin/env python3
"""
Debug helper script for Eplucon Home Assistant integration.
This script helps diagnose sensor update issues by providing detailed logging and diagnostics.

Usage:
1. Enable debug logging in Home Assistant configuration.yaml:
   logger:
     default: info
     logs:
       custom_components.eplucon: debug

2. Run this script to test API connectivity independently.
"""

import asyncio
import aiohttp
import logging
import sys
from datetime import datetime
from typing import Optional

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('eplucon_debug.log')
    ]
)

logger = logging.getLogger('eplucon_debug')

class EpluconDebugClient:
    """Simplified debug client for testing Eplucon API connectivity."""
    
    def __init__(self, api_token: str, api_endpoint: str = "https://portaal.eplucon.nl/api/v2"):
        self.api_token = api_token
        self.base_url = api_endpoint
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "Accept": "application/json",
            "Cache-Control": "no-cache",
            "Authorization": f"Bearer {api_token}"
        }
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def test_api_connection(self):
        """Test basic API connectivity and authentication."""
        logger.info("=" * 60)
        logger.info("EPLUCON API CONNECTION TEST")
        logger.info("=" * 60)
        logger.info(f"API Endpoint: {self.base_url}")
        logger.info(f"Timestamp: {datetime.now().isoformat()}")
        
        try:
            url = f"{self.base_url}/econtrol/modules"
            logger.info(f"Testing connection to: {url}")
            
            async with self.session.get(url, headers=self.headers) as response:
                logger.info(f"Response Status: {response.status}")
                logger.info(f"Response Headers: {dict(response.headers)}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ API Connection Successful!")
                    logger.info(f"Auth Status: {data.get('auth', 'NOT_FOUND')}")
                    devices = data.get('data', [])
                    logger.info(f"Devices Found: {len(devices)}")
                    
                    for i, device in enumerate(devices):
                        logger.info(f"Device {i+1}: ID={device.get('id')}, Name={device.get('name')}, Type={device.get('type')}")
                    
                    return devices
                else:
                    logger.error(f"❌ API Connection Failed: HTTP {response.status}")
                    error_text = await response.text()
                    logger.error(f"Error Response: {error_text}")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ Connection Exception: {type(e).__name__}: {e}")
            return None

    async def test_device_data(self, device_id: int):
        """Test fetching realtime data for a specific device."""
        logger.info("=" * 60)
        logger.info(f"TESTING DEVICE DATA - ID: {device_id}")
        logger.info("=" * 60)
        
        # Test realtime info
        try:
            url = f"{self.base_url}/econtrol/modules/{device_id}/get_realtime_info"
            logger.info(f"Fetching realtime info: {url}")
            
            async with self.session.get(url, headers=self.headers) as response:
                logger.info(f"Realtime Info Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Realtime Info Retrieved Successfully!")
                    
                    common_data = data.get('data', {}).get('common', {})
                    logger.info(f"Indoor Temperature: {common_data.get('indoor_temperature')}")
                    logger.info(f"Outdoor Temperature: {common_data.get('outdoor_temperature')}")
                    logger.info(f"Operation Mode: {common_data.get('operation_mode')}")
                    logger.info(f"Total Active Power: {common_data.get('total_active_power')}")
                    
                    # Check for None values that might cause sensor issues
                    none_values = [key for key, value in common_data.items() if value is None]
                    if none_values:
                        logger.warning(f"⚠️ Found None values for: {none_values}")
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Realtime Info Failed: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Realtime Info Exception: {type(e).__name__}: {e}")

        # Test heatloading status
        try:
            url = f"{self.base_url}/econtrol/modules/{device_id}/heatloading_status"
            logger.info(f"Fetching heatloading status: {url}")
            
            async with self.session.get(url, headers=self.headers) as response:
                logger.info(f"Heatloading Status Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info("✅ Heatloading Status Retrieved Successfully!")
                    
                    heatloading_data = data.get('data', {})
                    logger.info(f"Heatloading Active: {heatloading_data.get('heatloading_active')}")
                    logger.info(f"Configurations: {heatloading_data.get('configurations')}")
                    
                else:
                    error_text = await response.text()
                    logger.error(f"❌ Heatloading Status Failed: HTTP {response.status} - {error_text}")
                    
        except Exception as e:
            logger.error(f"❌ Heatloading Status Exception: {type(e).__name__}: {e}")

    async def run_full_diagnostic(self):
        """Run complete diagnostic test."""
        logger.info("🔍 Starting Eplucon Integration Diagnostic")
        
        # Test API connection
        devices = await self.test_api_connection()
        
        if devices:
            # Test each device
            for device in devices:
                device_id = device.get('id')
                if device_id:
                    await self.test_device_data(device_id)
                    
        logger.info("🏁 Diagnostic Complete!")
        logger.info("Check 'eplucon_debug.log' for detailed output.")


async def main():
    """Main function to run diagnostic."""
    print("Eplucon Home Assistant Integration Debug Tool")
    print("=" * 50)
    
    # Get API token from user
    api_token = input("Enter your Eplucon API token: ").strip()
    if not api_token:
        print("❌ API token is required!")
        return
    
    # Optional custom endpoint
    api_endpoint = input("Enter API endpoint (press Enter for default): ").strip()
    if not api_endpoint:
        api_endpoint = "https://portaal.eplucon.nl/api/v2"
    
    try:
        async with EpluconDebugClient(api_token, api_endpoint) as client:
            await client.run_full_diagnostic()
    except KeyboardInterrupt:
        logger.info("Diagnostic interrupted by user")
    except Exception as e:
        logger.error(f"Diagnostic failed: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
