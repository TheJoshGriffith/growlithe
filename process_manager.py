"""
Process Manager
Handles process monitoring, starting, stopping, and restarting on Android devices
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from config import Config, DeviceConfig
from device_manager import DeviceManager
from log_tailer import LogTailer


@dataclass
class ProcessStatus:
    """Status information for a process on a device"""
    device_ip: str
    device_port: int
    process_name: str
    running: bool
    pid: Optional[int] = None
    start_time: Optional[float] = None
    restart_count: int = 0
    last_restart: Optional[float] = None
    last_error: Optional[str] = None


class ProcessManager:
    """Manages process lifecycle on Android devices"""
    
    def __init__(self, config: Config):
        """Initialize process manager with configuration"""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.device_manager = DeviceManager(config)
        self.log_tailer = LogTailer(self.device_manager)
        self.process_statuses: Dict[str, ProcessStatus] = {}
        self.restart_attempts: Dict[str, int] = {}
        
        for device in config.get_devices():
            device_key = f"{device.ip}:{device.port}"
            if device.process_name:
                process_key = f"{device_key}:{device.process_name}"
                self.process_statuses[process_key] = ProcessStatus(
                    device_ip=device.ip,
                    device_port=device.port,
                    process_name=device.process_name,
                    running=False
                )
                self.restart_attempts[process_key] = 0
    
    async def manage_process(self, ip: str, port: int, device_config: DeviceConfig):
        """Manage a process on a specific device"""
        device_key = f"{ip}:{port}"
        process_key = f"{device_key}:{device_config.process_name}"
        
        if not device_config.process_name:
            self.logger.warning(f"No process name configured for device {device_key}")
            return
        
        try:
            is_running = await self._is_process_running(ip, port, device_config.process_name)
            
            if is_running:
                await self._update_process_status(process_key, running=True)
                self.logger.debug(f"Process {device_config.process_name} is running on {device_key}")
            else:
                await self._update_process_status(process_key, running=False)
                
                if device_config.restart_on_failure:
                    await self._handle_process_restart(ip, port, device_config, process_key)
                else:
                    self.logger.info(f"Process {device_config.process_name} not running on {device_key} (restart disabled)")
        
        except Exception as e:
            self.logger.error(f"Error managing process on {device_key}: {e}")
            await self._update_process_status(process_key, running=False, error=str(e))
    
    async def _is_process_running(self, ip: str, port: int, process_name: str) -> bool:
        """Check if a process is running on a device"""
        try:
            command = f"ps -A | grep '{process_name}' | grep -v grep"
            result = await self.device_manager.run_shell_command(ip, port, command)
            
            if result and result.strip():
                lines = result.strip().split('\n')
                for line in lines:
                    if process_name in line:
                        parts = line.split()
                        if len(parts) >= 2:
                            try:
                                pid = int(parts[1])
                                await self._update_process_status(
                                    f"{ip}:{port}:{process_name}",
                                    running=True,
                                    pid=pid,
                                    start_time=time.time()
                                )
                                return True
                            except (ValueError, IndexError):
                                pass
                return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking process status: {e}")
            return False
    
    async def _handle_process_restart(self, ip: str, port: int, device_config: DeviceConfig, process_key: str):
        """Handle process restart logic"""
        device_key = f"{ip}:{port}"
        current_attempts = self.restart_attempts.get(process_key, 0)
        
        if current_attempts >= device_config.max_restart_attempts:
            self.logger.warning(
                f"Max restart attempts ({device_config.max_restart_attempts}) reached for "
                f"{device_config.process_name} on {device_key}"
            )
            return
        
        process_status = self.process_statuses.get(process_key)
        if process_status and process_status.last_restart:
            time_since_restart = time.time() - process_status.last_restart
            if time_since_restart < device_config.restart_delay:
                self.logger.debug(
                    f"Waiting {device_config.restart_delay - time_since_restart:.1f}s before restarting "
                    f"{device_config.process_name} on {device_key}"
                )
                return
        
        self.logger.info(f"Starting process {device_config.process_name} on {device_key}")
        
        if await self._start_process(ip, port, device_config):
            self.restart_attempts[process_key] = 0
            await self._update_process_status(
                process_key,
                running=True,
                start_time=time.time(),
                last_restart=time.time()
            )
            self.logger.info(f"Successfully started {device_config.process_name} on {device_key}")
        else:
            self.restart_attempts[process_key] = current_attempts + 1
            await self._update_process_status(
                process_key,
                running=False,
                last_restart=time.time(),
                restart_count=current_attempts + 1
            )
            self.logger.error(f"Failed to start {device_config.process_name} on {device_key}")
    
    async def _start_process(self, ip: str, port: int, device_config: DeviceConfig) -> bool:
        """Start a process on a device"""
        device_key = f"{ip}:{port}"
        
        try:
            if not device_config.binary_path:
                self.logger.error(f"No binary path configured for device {device_key}")
                return False
            
            if not device_config.working_directory:
                self.logger.error(f"No working directory configured for device {device_key}")
                return False
            
            command_parts = []
            
            if device_config.environment_vars:
                env_vars = []
                for key, value in device_config.environment_vars.items():
                    env_vars.append(f"{key}={value}")
                command_parts.append(" ".join(env_vars))
            
            command_parts.append(f"cd {device_config.working_directory}")
            command_parts.append(f"nohup {device_config.binary_path} > /data/local/tmp/{device_config.process_name}.log 2>&1 &")
            
            full_command = " && ".join(command_parts)
            
            su_command = f"su -c '{full_command}'"
            
            result = await self.device_manager.run_shell_command(ip, port, su_command)
            
            if result is not None:
                self.logger.debug(f"Process start command executed on {device_key}")
                
                await asyncio.sleep(2)
                
                if await self._is_process_running(ip, port, device_config.process_name):
                    return True
                else:
                    self.logger.warning(f"Process start command executed but process not found on {device_key}")
                    return False
            else:
                self.logger.error(f"Failed to execute process start command on {device_key}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error starting process on {device_key}: {e}")
            return False
    
    async def stop_process(self, ip: str, port: int, process_name: str) -> bool:
        """Stop a process on a device"""
        device_key = f"{ip}:{port}"
        
        try:
            command = f"ps -A | grep '{process_name}' | grep -v grep"
            result = await self.device_manager.run_shell_command(ip, port, command)
            
            if not result or not result.strip():
                self.logger.info(f"Process {process_name} not running on {device_key}")
                return True
            
            lines = result.strip().split('\n')
            for line in lines:
                if process_name in line:
                    parts = line.split()
                    if len(parts) >= 2:
                        try:
                            pid = int(parts[1])
                            kill_command = f"su -c 'kill {pid}'"
                            await self.device_manager.run_shell_command(ip, port, kill_command)
                            self.logger.info(f"Stopped process {process_name} (PID: {pid}) on {device_key}")
                            return True
                        except (ValueError, IndexError):
                            continue
            
            kill_command = f"su -c 'pkill -f {process_name}'"
            await self.device_manager.run_shell_command(ip, port, kill_command)
            self.logger.info(f"Stopped process {process_name} on {device_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error stopping process on {device_key}: {e}")
            return False
    
    async def restart_process(self, ip: str, port: int, process_name: str) -> bool:
        """Restart a process on a device"""
        device_key = f"{ip}:{port}"
        
        self.logger.info(f"Restarting process {process_name} on {device_key}")
        
        await self.stop_process(ip, port, process_name)
        
        await asyncio.sleep(2)
        
        device_config = self.config.get_device(ip, port)
        if device_config:
            return await self._start_process(ip, port, device_config)
        else:
            self.logger.error(f"No device configuration found for {device_key}")
            return False
    
    async def _update_process_status(self, process_key: str, **kwargs):
        """Update process status information"""
        if process_key in self.process_statuses:
            status = self.process_statuses[process_key]
            for key, value in kwargs.items():
                if hasattr(status, key):
                    setattr(status, key, value)
    
    def get_process_status(self, ip: str, port: int, process_name: str) -> Optional[ProcessStatus]:
        """Get status information for a process"""
        process_key = f"{ip}:{port}:{process_name}"
        return self.process_statuses.get(process_key)
    
    def get_all_process_statuses(self) -> Dict[str, ProcessStatus]:
        """Get status information for all processes"""
        return self.process_statuses.copy()
    
    def get_running_processes(self) -> List[ProcessStatus]:
        """Get list of running processes"""
        return [status for status in self.process_statuses.values() if status.running]
    
    def get_failed_processes(self) -> List[ProcessStatus]:
        """Get list of failed processes"""
        return [status for status in self.process_statuses.values() 
                if not status.running and status.last_error]
    
    async def start_log_tailing(self):
        """Start log tailing for all devices"""
        devices = self.config.get_devices()
        await self.log_tailer.start_all_tailers(devices)
    
    async def stop_log_tailing(self):
        """Stop log tailing for all devices"""
        await self.log_tailer.stop_all_tailers()
    
    def get_log_tailer_status(self, ip: str, port: int = 5555):
        """Get log tailer status for a device"""
        return self.log_tailer.get_tailer_status(ip, port)
    
    def get_all_log_tailer_statuses(self):
        """Get status of all log tailers"""
        return self.log_tailer.get_all_tailer_statuses()
    
    async def cleanup(self):
        """Cleanup resources"""
        self.logger.info("Cleaning up process manager...")
        await self.log_tailer.cleanup()
        await self.device_manager.cleanup()
        self.logger.info("Process manager cleanup completed")
    
    def __str__(self) -> str:
        """String representation of process manager"""
        running_count = len(self.get_running_processes())
        total_count = len(self.process_statuses)
        return f"ProcessManager(running: {running_count}/{total_count})"
