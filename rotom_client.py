"""
Rotom API Client
Handles communication with Rotom API for device and worker status monitoring
"""

import asyncio
import logging
import aiohttp
import toml
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from config import DeviceConfig
from device_manager import DeviceManager


@dataclass
class WorkerInfo:
    """Information about a worker"""
    worker_id: str
    device_id: str
    status: str
    last_seen: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DeviceInfo:
    """Information about a device from Rotom API"""
    device_id: str
    device_name: str
    workers: List[WorkerInfo]
    status: str
    last_seen: Optional[str] = None


@dataclass
class RotomStatus:
    """Complete status from Rotom API"""
    devices: List[DeviceInfo]
    total_workers: int
    active_workers: int
    timestamp: Optional[str] = None


class RotomClient:
    """Client for communicating with Rotom API"""
    
    def __init__(self, device_manager: DeviceManager):
        """Initialize Rotom client with device manager"""
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_status(self, rotom_url: str) -> Optional[RotomStatus]:
        """Get status from Rotom API"""
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        url = f"http://{rotom_url}/api/status"
        
        try:
            async with self.session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_status_response(data)
                else:
                    self.logger.error(f"Rotom API returned status {response.status}")
                    return None
        except Exception as e:
            self.logger.error(f"Error fetching Rotom status: {e}")
            return None
    
    def _parse_status_response(self, data: Dict[str, Any]) -> RotomStatus:
        """Parse the JSON response from Rotom API"""
        devices = []
        total_workers = 0
        active_workers = 0
        
        devices_list = data.get('devices', [])
        workers_list = data.get('workers', [])
        
        workers_by_device = {}
        for worker_data in workers_list:
            device_id = worker_data.get('deviceId', '')
            if device_id not in workers_by_device:
                workers_by_device[device_id] = []
            
            worker_id = worker_data.get('workerId', '')
            worker_info = worker_data.get('worker', {})
            is_alive = worker_info.get('isAlive', False)
            
            worker = WorkerInfo(
                worker_id=worker_id,
                device_id=device_id,
                status='active' if is_alive else 'inactive',
                last_seen=worker_data.get('dateLastMessageReceived'),
                metadata=worker_info
            )
            workers_by_device[device_id].append(worker)
            
            total_workers += 1
            if is_alive:
                active_workers += 1
        
        for device_data in devices_list:
            device_id = device_data.get('deviceId', '')
            device_name = device_id
            device_status = 'alive' if device_data.get('isAlive', False) else 'dead'
            workers = workers_by_device.get(device_id, [])
            
            device = DeviceInfo(
                device_id=device_id,
                device_name=device_name,
                workers=workers,
                status=device_status,
                last_seen=device_data.get('dateLastMessageReceived')
            )
            devices.append(device)
        
        return RotomStatus(
            devices=devices,
            total_workers=total_workers,
            active_workers=active_workers,
            timestamp=data.get('timestamp')
        )
    
    async def get_device_config(self, device_config: DeviceConfig) -> Optional[Dict[str, Any]]:
        """Get device configuration from TOML file on device"""
        try:
            config_path = device_config.config_path
            cat_command = f"cat {config_path}"
            
            result = await self.device_manager.run_shell_command(
                device_config.ip, device_config.port, cat_command
            )
            
            if result:
                config_data = toml.loads(result)
                return config_data
            else:
                self.logger.warning(f"Could not read config file from {device_config.ip}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error reading device config from {device_config.ip}: {e}")
            return None
    
    def extract_device_name(self, config_data: Dict[str, Any]) -> Optional[str]:
        """Extract device name from TOML config"""
        try:
            general_section = config_data.get('general', {})
            device_name = general_section.get('device_name')
            return device_name
        except Exception as e:
            self.logger.error(f"Error extracting device name: {e}")
            return None
    
    def find_device_by_name(self, rotom_status: RotomStatus, device_name: str) -> Optional[DeviceInfo]:
        """Find a device in Rotom status by device name"""
        for device in rotom_status.devices:
            if device.device_name == device_name:
                return device
        return None
    
    def has_active_workers(self, device_info: DeviceInfo) -> bool:
        """Check if a device has any active workers"""
        for worker in device_info.workers:
            if worker.status in ['active', 'running', 'connected']:
                return True
        return False
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
            self.session = None


class RotomMonitor:
    """Monitor that integrates Rotom status with device management"""
    
    def __init__(self, device_manager: DeviceManager, process_manager):
        """Initialize Rotom monitor"""
        self.device_manager = device_manager
        self.process_manager = process_manager
        self.logger = logging.getLogger(__name__)
        self.rotom_client: Optional[RotomClient] = None
        
    async def start_monitoring(self, device_configs: List[DeviceConfig]):
        """Start monitoring devices with Rotom integration"""
        self.rotom_client = RotomClient(self.device_manager)
        
        async with self.rotom_client:
            while True:
                try:
                    await self._monitor_cycle(device_configs)
                    await asyncio.sleep(30)
                except Exception as e:
                    self.logger.error(f"Error in Rotom monitoring cycle: {e}")
                    await asyncio.sleep(10)
    
    async def _monitor_cycle(self, device_configs: List[DeviceConfig]):
        """Single monitoring cycle"""
        if not device_configs:
            return
            
        rotom_url = device_configs[0].rotom_url
        rotom_status = await self.rotom_client.get_status(rotom_url)
        
        if not rotom_status:
            self.logger.warning("Could not fetch Rotom status")
            return
        
        self.logger.info(f"Rotom status: {rotom_status.active_workers}/{rotom_status.total_workers} active workers")
        
        for device_config in device_configs:
            await self._check_device_status(device_config, rotom_status)
    
    async def _check_device_status(self, device_config: DeviceConfig, rotom_status: RotomStatus):
        """Check status of a single device"""
        try:
            config_data = await self.rotom_client.get_device_config(device_config)
            if not config_data:
                self.logger.warning(f"Could not get config for device {device_config.ip}")
                return
            
            device_name = self.rotom_client.extract_device_name(config_data)
            if not device_name:
                self.logger.warning(f"Could not extract device name for {device_config.ip}")
                return
            
            device_info = self.rotom_client.find_device_by_name(rotom_status, device_name)
            if not device_info:
                self.logger.warning(f"Device {device_name} not found in Rotom status")
                return
            
            has_workers = self.rotom_client.has_active_workers(device_info)
            
            if not has_workers:
                self.logger.warning(f"Device {device_name} ({device_config.ip}) has no active workers, restarting process")
                await self._restart_device_process(device_config)
            else:
                self.logger.debug(f"Device {device_name} ({device_config.ip}) has {len(device_info.workers)} active workers")
                
        except Exception as e:
            self.logger.error(f"Error checking device {device_config.ip}: {e}")
    
    async def _restart_device_process(self, device_config: DeviceConfig):
        """Restart the process on a device"""
        try:
            await self.process_manager.stop_process(
                device_config.ip, device_config.port, device_config.process_name
            )
            
            await asyncio.sleep(2)
            
            await self.process_manager.manage_process(
                device_config.ip, device_config.port, device_config
            )
            
            self.logger.info(f"Restarted process on device {device_config.ip}")
            
        except Exception as e:
            self.logger.error(f"Error restarting process on device {device_config.ip}: {e}")
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.rotom_client:
            await self.rotom_client.cleanup()
