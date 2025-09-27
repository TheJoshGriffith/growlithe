#!/usr/bin/env python3
"""
Android Device Monitor and Controller
Main entry point for the application
"""

import asyncio
import logging
import signal
import sys
from typing import List

from config import Config
from device_manager import DeviceManager
from process_manager import ProcessManager
from rotom_client import RotomMonitor


class AndroidMonitor:
    """Main application class for monitoring and controlling Android devices"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the Android monitor with configuration"""
        self.config = Config(config_path)
        self.device_manager = DeviceManager(self.config)
        self.process_manager = ProcessManager(self.config)
        self.rotom_monitor = RotomMonitor(self.device_manager, self.process_manager)
        self.running = False
        
        self._setup_logging()
        
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
    
    def _setup_logging(self):
        """Configure logging for the application"""
        log_level = getattr(logging, self.config.get('logging.level', 'INFO').upper())
        log_format = self.config.get('logging.format', 
                                   '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        logging.basicConfig(
            level=log_level,
            format=log_format,
            handlers=[
                logging.StreamHandler(sys.stdout),
                logging.FileHandler('android_monitor.log')
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Android Monitor initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running = False
    
    async def start_monitoring(self):
        """Start the monitoring loop"""
        self.running = True
        self.logger.info("Starting Android device monitoring...")
        
        await self.process_manager.start_log_tailing()
        
        devices = self.config.get_devices()
        rotom_task = asyncio.create_task(self.rotom_monitor.start_monitoring(devices))
        
        try:
            while self.running:
                await self._monitor_cycle()
                await asyncio.sleep(self.config.get('monitoring.interval', 30))
        except Exception as e:
            self.logger.error(f"Error in monitoring loop: {e}")
        finally:
            rotom_task.cancel()
            await self.cleanup()
    
    async def _monitor_cycle(self):
        """Single monitoring cycle - check devices and processes"""
        try:
            devices = self.config.get_devices()
            
            for device_config in devices:
                device_ip = device_config.ip
                device_port = device_config.port
                device_name = device_config.name or f"{device_ip}:{device_port}"
                
                self.logger.debug(f"Checking device: {device_name}")
                
                if await self.device_manager.is_device_online(device_ip, device_port):
                    self.logger.info(f"Device {device_name} is online")
                    
                    await self.process_manager.manage_process(device_ip, device_port, device_config)
                else:
                    self.logger.warning(f"Device {device_name} is offline")
                    
        except Exception as e:
            self.logger.error(f"Error in monitoring cycle: {e}")
    
    async def cleanup(self):
        """Cleanup resources before shutdown"""
        self.logger.info("Cleaning up resources...")
        await self.process_manager.stop_log_tailing()
        await self.rotom_monitor.cleanup()
        await self.device_manager.cleanup()
        await self.process_manager.cleanup()
    
    def run_once(self):
        """Run a single monitoring cycle (useful for testing)"""
        return asyncio.run(self._monitor_cycle())
    
    def run_continuous(self):
        """Run continuous monitoring"""
        return asyncio.run(self.start_monitoring())


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Android Device Monitor and Controller")
    parser.add_argument('--config', '-c', default='config.yaml',
                       help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--once', action='store_true',
                       help='Run once instead of continuous monitoring')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    try:
        monitor = AndroidMonitor(args.config)
        
        if args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        if args.once:
            monitor.run_once()
        else:
            monitor.run_continuous()
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
