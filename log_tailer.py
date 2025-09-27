"""
Log Tailer for Android Device Monitor
Handles real-time log file monitoring from Android devices
"""

import asyncio
import logging
import time
from typing import Dict, Set, Optional
from dataclasses import dataclass

from device_manager import DeviceManager
from config import DeviceConfig


@dataclass
class LogTailerStatus:
    """Status information for a log tailer"""
    device_ip: str
    device_port: int
    log_path: str
    active: bool = True
    last_read_position: int = 0
    last_activity: float = 0.0
    error_count: int = 0
    last_error: Optional[str] = None


class LogTailer:
    """Manages real-time log tailing from Android devices"""
    
    def __init__(self, device_manager: DeviceManager):
        """Initialize log tailer with device manager"""
        self.device_manager = device_manager
        self.logger = logging.getLogger(__name__)
        self.tailer_statuses: Dict[str, LogTailerStatus] = {}
        self.active_tailers: Set[str] = set()
        self.running = True
    
    async def start_tailing(self, device_config: DeviceConfig):
        """Start tailing logs for a specific device"""
        device_key = f"{device_config.ip}:{device_config.port}"
        
        if device_key in self.active_tailers:
            self.logger.debug(f"Log tailer already active for {device_key}")
            return
        
        self.logger.info(f"Starting log tailer for {device_key} -> {device_config.log_path}")
        
        self.tailer_statuses[device_key] = LogTailerStatus(
            device_ip=device_config.ip,
            device_port=device_config.port,
            log_path=device_config.log_path,
            active=True,
            last_activity=time.time()
        )
        
        self.active_tailers.add(device_key)
        asyncio.create_task(self._tail_log_file(device_config))
    
    async def stop_tailing(self, device_ip: str, device_port: int = 5555):
        """Stop tailing logs for a specific device"""
        device_key = f"{device_ip}:{device_port}"
        
        if device_key in self.tailer_statuses:
            self.tailer_statuses[device_key].active = False
            self.active_tailers.discard(device_key)
            self.logger.info(f"Stopped log tailer for {device_key}")
    
    async def start_all_tailers(self, device_configs: list[DeviceConfig]):
        """Start log tailing for all devices"""
        self.logger.info(f"Starting log tailers for {len(device_configs)} devices")
        
        for device_config in device_configs:
            if device_config.log_path:
                await self.start_tailing(device_config)
    
    async def _tail_log_file(self, device_config: DeviceConfig):
        """Background task to tail a log file from a device"""
        device_key = f"{device_config.ip}:{device_config.port}"
        log_path = device_config.log_path
        
        try:
            while self.running:
                status = self.tailer_statuses.get(device_key)
                if not status or not status.active:
                    break
                
                try:
                    if not await self.device_manager.is_device_online(device_config.ip, device_config.port):
                        self.logger.debug(f"Device {device_key} offline, pausing log tailing")
                        await asyncio.sleep(5)
                        continue
                    
                    size_command = f"stat -c %s {log_path} 2>/dev/null || echo 0"
                    size_result = await self.device_manager.run_shell_command(
                        device_config.ip, device_config.port, size_command
                    )
                    
                    if not size_result:
                        await asyncio.sleep(2)
                        continue
                    
                    try:
                        current_size = int(size_result.strip())
                    except (ValueError, AttributeError):
                        current_size = 0
                    
                    if current_size < status.last_read_position:
                        status.last_read_position = 0
                        self.logger.info(f"Log file {log_path} on {device_key} was truncated, resetting position")
                    
                    if current_size > status.last_read_position:
                        tail_command = f"tail -c +{status.last_read_position + 1} {log_path} 2>/dev/null"
                        content_result = await self.device_manager.run_shell_command(
                            device_config.ip, device_config.port, tail_command
                        )
                        
                        if content_result and content_result.strip():
                            if device_config.log_emission_enabled:
                                lines = content_result.strip().split('\n')
                                for line in lines:
                                    if line.strip():
                                        print(f"[{device_key}] {line}")
                            
                            status.last_read_position = current_size
                            status.last_activity = time.time()
                            status.error_count = 0
                            status.last_error = None
                    
                    await asyncio.sleep(1)
                    
                except Exception as e:
                    status.error_count += 1
                    status.last_error = str(e)
                    self.logger.error(f"Error tailing log for {device_key}: {e}")
                    
                    delay = min(2 ** status.error_count, 30)
                    await asyncio.sleep(delay)
        
        except Exception as e:
            self.logger.error(f"Fatal error in log tailing task for {device_key}: {e}")
        finally:
            self.active_tailers.discard(device_key)
            if device_key in self.tailer_statuses:
                self.tailer_statuses[device_key].active = False
            self.logger.debug(f"Log tailing task ended for {device_key}")
    
    async def stop_all_tailers(self):
        """Stop all log tailers"""
        self.running = False
        self.logger.info("Stopping all log tailers")
        
        for device_key in list(self.active_tailers):
            status = self.tailer_statuses.get(device_key)
            if status:
                await self.stop_tailing(status.device_ip, status.device_port)
        
        while self.active_tailers:
            await asyncio.sleep(0.1)
        
        self.logger.info("All log tailers stopped")
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.stop_all_tailers()
    
    def __str__(self) -> str:
        """String representation of log tailer"""
        active_count = len(self.active_tailers)
        total_count = len(self.tailer_statuses)
        return f"LogTailer(active: {active_count}/{total_count})"
