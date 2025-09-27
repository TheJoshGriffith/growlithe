"""
Android Device Manager
Handles ADB connections and device state management
"""

import asyncio
import logging
import subprocess
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import Config, DeviceConfig


@dataclass
class DeviceStatus:
    """Status information for an Android device"""
    ip: str
    port: int
    connected: bool
    online: bool
    last_seen: float
    error_count: int = 0
    last_error: Optional[str] = None


class DeviceManager:
    """Manages Android device connections and status monitoring"""
    
    def __init__(self, config: Config):
        """Initialize device manager with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.device_statuses: Dict[str, DeviceStatus] = {}
        self.adb_path = config.get('adb.path', 'adb')
        self.connect_timeout = config.get('adb.connect_timeout', 10)
        self.command_timeout = config.get('adb.command_timeout', 30)
        
        for device in config.get_devices():
            device_key = f"{device.ip}:{device.port}"
            self.device_statuses[device_key] = DeviceStatus(
                ip=device.ip,
                port=device.port,
                connected=False,
                online=False,
                last_seen=0.0
            )
    
    async def is_device_online(self, ip: str, port: int = 5555) -> bool:
        """Check if a device is online and accessible"""
        device_key = f"{ip}:{port}"
        device_status = self.device_statuses.get(device_key)
        
        if not device_status:
            self.logger.warning(f"Unknown device: {device_key}")
            return False
        
        try:
            if not await self._connect_device(ip, port):
                device_status.connected = False
                device_status.online = False
                return False
            
            result = await self._run_adb_command(f"-s {ip}:{port} get-state")
            
            if result and result.strip() == "device":
                device_status.connected = True
                device_status.online = True
                device_status.last_seen = time.time()
                device_status.error_count = 0
                device_status.last_error = None
                return True
            else:
                device_status.connected = False
                device_status.online = False
                self.logger.debug(f"Device {device_key} state: {result}")
                return False
                
        except Exception as e:
            device_status.connected = False
            device_status.online = False
            device_status.error_count += 1
            device_status.last_error = str(e)
            self.logger.error(f"Error checking device {device_key}: {e}")
            return False
    
    async def _connect_device(self, ip: str, port: int = 5555) -> bool:
        """Connect to a device via ADB"""
        device_key = f"{ip}:{port}"
        
        try:
            result = await self._run_adb_command(f"connect {ip}:{port}")
            
            if result and "connected" in result.lower():
                self.logger.debug(f"Successfully connected to {device_key}")
                return True
            else:
                self.logger.debug(f"Failed to connect to {device_key}: {result}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error connecting to {device_key}: {e}")
            return False
    
    async def disconnect_device(self, ip: str, port: int = 5555) -> bool:
        """Disconnect from a device"""
        device_key = f"{ip}:{port}"
        
        try:
            result = await self._run_adb_command(f"disconnect {ip}:{port}")
            self.logger.info(f"Disconnected from {device_key}")
            return True
        except Exception as e:
            self.logger.error(f"Error disconnecting from {device_key}: {e}")
            return False
    
    async def get_device_info(self, ip: str, port: int = 5555) -> Optional[Dict[str, str]]:
        """Get detailed information about a device"""
        device_key = f"{ip}:{port}"
        
        if not await self.is_device_online(ip, port):
            return None
        
        try:
            info = {}
            
            model = await self._run_adb_command(f"-s {ip}:{port} shell getprop ro.product.model")
            if model:
                info['model'] = model.strip()
            
            version = await self._run_adb_command(f"-s {ip}:{port} shell getprop ro.build.version.release")
            if version:
                info['android_version'] = version.strip()
            
            device_id = await self._run_adb_command(f"-s {ip}:{port} shell getprop ro.serialno")
            if device_id:
                info['device_id'] = device_id.strip()
            
            battery = await self._run_adb_command(f"-s {ip}:{port} shell dumpsys battery | grep level")
            if battery:
                try:
                    battery_level = battery.split(':')[1].strip()
                    info['battery_level'] = battery_level
                except:
                    pass
            
            return info
            
        except Exception as e:
            self.logger.error(f"Error getting device info for {device_key}: {e}")
            return None
    
    async def run_shell_command(self, ip: str, port: int, command: str) -> Optional[str]:
        """Run a shell command on a device"""
        device_key = f"{ip}:{port}"
        
        if not await self.is_device_online(ip, port):
            self.logger.error(f"Cannot run command on offline device: {device_key}")
            return None
        
        try:
            full_command = f"-s {ip}:{port} shell {command}"
            result = await self._run_adb_command(full_command)
            return result
        except Exception as e:
            self.logger.error(f"Error running command on {device_key}: {e}")
            return None
    
    async def _run_adb_command(self, command: str) -> Optional[str]:
        """Run an ADB command and return the output"""
        full_command = f"{self.adb_path} {command}"
        
        try:
            process = await asyncio.create_subprocess_shell(
                full_command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(),
                timeout=self.command_timeout
            )
            
            if process.returncode == 0:
                return stdout.decode('utf-8', errors='ignore')
            else:
                error_msg = stderr.decode('utf-8', errors='ignore')
                self.logger.debug(f"ADB command failed: {full_command}, error: {error_msg}")
                return None
                
        except asyncio.TimeoutError:
            self.logger.error(f"ADB command timeout: {full_command}")
            return None
        except Exception as e:
            self.logger.error(f"Error running ADB command: {full_command}, error: {e}")
            return None
    
    def get_device_status(self, ip: str, port: int = 5555) -> Optional[DeviceStatus]:
        """Get status information for a device"""
        device_key = f"{ip}:{port}"
        return self.device_statuses.get(device_key)
    
    def get_all_device_statuses(self) -> Dict[str, DeviceStatus]:
        """Get status information for all devices"""
        return self.device_statuses.copy()
    
    def get_online_devices(self) -> List[Tuple[str, int]]:
        """Get list of online devices"""
        online_devices = []
        for device_key, status in self.device_statuses.items():
            if status.online:
                online_devices.append((status.ip, status.port))
        return online_devices
    
    def get_offline_devices(self) -> List[Tuple[str, int]]:
        """Get list of offline devices"""
        offline_devices = []
        for device_key, status in self.device_statuses.items():
            if not status.online:
                offline_devices.append((status.ip, status.port))
        return offline_devices
    
    async def restart_adb_server(self) -> bool:
        """Restart the ADB server"""
        try:
            self.logger.info("Restarting ADB server...")
            result = await self._run_adb_command("kill-server")
            await asyncio.sleep(1)
            result = await self._run_adb_command("start-server")
            self.logger.info("ADB server restarted")
            return True
        except Exception as e:
            self.logger.error(f"Error restarting ADB server: {e}")
            return False
    
    async def cleanup(self):
        """Cleanup resources and disconnect from devices"""
        self.logger.info("Cleaning up device manager...")
        
        for device_key, status in self.device_statuses.items():
            if status.connected:
                await self.disconnect_device(status.ip, status.port)
        
        self.logger.info("Device manager cleanup completed")
    
    def __str__(self) -> str:
        """String representation of device manager"""
        online_count = len(self.get_online_devices())
        total_count = len(self.device_statuses)
        return f"DeviceManager(online: {online_count}/{total_count})"
