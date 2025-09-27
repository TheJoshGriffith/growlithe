"""
Configuration management for Android Device Monitor
Handles loading and validation of configuration files
"""

import os
import yaml
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class DeviceDefaults:
    """Global default values for device configuration"""
    port: int = 5555
    process_name: str = "com.nianticlabs.pokemongo"
    binary_path: str = "/data/local/tmp/newcosmog/com.nianticlabs.pokemongo"
    working_directory: str = "/data/local/tmp/newcosmog"
    log_path: str = "/data/local/tmp/cosmog.log"
    log_emission_enabled: bool = False
    rotom_url: str = "harris.lan:7072"
    config_path: str = "/data/local/tmp/newcosmog/config.toml"
    environment_vars: Dict[str, str] = field(default_factory=lambda: {"LD_LIBRARY_PATH": "./lib"})
    restart_on_failure: bool = True
    max_restart_attempts: int = 3
    restart_delay: int = 5


@dataclass
class DeviceConfig:
    """Configuration for a single Android device"""
    ip: str
    port: Optional[int] = None
    name: Optional[str] = None
    binary_path: Optional[str] = None
    process_name: Optional[str] = None
    working_directory: Optional[str] = None
    log_path: Optional[str] = None
    log_emission_enabled: Optional[bool] = None
    rotom_url: Optional[str] = None
    config_path: Optional[str] = None
    environment_vars: Optional[Dict[str, str]] = None
    restart_on_failure: Optional[bool] = None
    max_restart_attempts: Optional[int] = None
    restart_delay: Optional[int] = None
    
    def apply_defaults(self, defaults: DeviceDefaults) -> 'DeviceConfig':
        """Apply global defaults to this device configuration"""
        return DeviceConfig(
            ip=self.ip,
            port=self.port or defaults.port,
            name=self.name or f"Device {self.ip}",
            binary_path=self.binary_path or defaults.binary_path,
            process_name=self.process_name or defaults.process_name,
            working_directory=self.working_directory or defaults.working_directory,
            log_path=self.log_path or defaults.log_path,
            log_emission_enabled=self.log_emission_enabled if self.log_emission_enabled is not None else defaults.log_emission_enabled,
            rotom_url=self.rotom_url or defaults.rotom_url,
            config_path=self.config_path or defaults.config_path,
            environment_vars=self.environment_vars or defaults.environment_vars.copy(),
            restart_on_failure=self.restart_on_failure if self.restart_on_failure is not None else defaults.restart_on_failure,
            max_restart_attempts=self.max_restart_attempts or defaults.max_restart_attempts,
            restart_delay=self.restart_delay or defaults.restart_delay
        )


@dataclass
class MonitoringConfig:
    """Configuration for monitoring behavior"""
    interval: int = 30  # seconds between checks
    timeout: int = 10   # seconds for device operations
    retry_attempts: int = 3
    retry_delay: int = 5


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "android_monitor.log"
    max_size: int = 10485760  # 10MB
    backup_count: int = 5


class Config:
    """Main configuration class for the Android Monitor application"""
    
    def __init__(self, config_path: str = "config.yaml"):
        """Initialize configuration from file"""
        self.config_path = config_path
        self._config_data = {}
        self._devices: List[DeviceConfig] = []
        self._device_defaults = DeviceDefaults()
        self._monitoring = MonitoringConfig()
        self._logging = LoggingConfig()
        
        self.load_config()
    
    def load_config(self):
        """Load configuration from YAML file"""
        if not os.path.exists(self.config_path):
            self._create_default_config()
            return
        
        try:
            with open(self.config_path, 'r') as file:
                self._config_data = yaml.safe_load(file) or {}
            
            self._parse_device_defaults()
            self._parse_devices()
            self._parse_monitoring()
            self._parse_logging()
            
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML configuration: {e}")
        except Exception as e:
            raise ValueError(f"Error loading configuration: {e}")
    
    def _create_default_config(self):
        """Create a default configuration file"""
        default_config = {
            'device_defaults': {
                'port': 5555,
                'process_name': 'com.nianticlabs.pokemongo',
                'binary_path': '/data/local/tmp/newcosmog/com.nianticlabs.pokemongo',
                'working_directory': '/data/local/tmp/newcosmog',
                'log_path': '/data/local/tmp/cosmog.log',
                'log_emission_enabled': False,
                'rotom_url': 'harris.lan:7072',
                'config_path': '/data/local/tmp/newcosmog/config.toml',
                'environment_vars': {
                    'LD_LIBRARY_PATH': './lib'
                },
                'restart_on_failure': True,
                'max_restart_attempts': 3,
                'restart_delay': 5
            },
            'devices': [
                {'ip': '10.0.1.50'},
                {'ip': '10.0.1.52'},
                {'ip': '10.0.1.53'}
            ],
            'monitoring': {
                'interval': 30,
                'timeout': 10,
                'retry_attempts': 3,
                'retry_delay': 5
            },
            'logging': {
                'level': 'INFO',
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'file': 'android_monitor.log',
                'max_size': 10485760,
                'backup_count': 5
            },
            'adb': {
                'path': 'adb',
                'connect_timeout': 10,
                'command_timeout': 30
            },
            'web': {
                'enabled': False,
                'host': '0.0.0.0',
                'port': 8080,
                'api_key': None
            }
        }
        
        try:
            with open(self.config_path, 'w') as file:
                yaml.dump(default_config, file, default_flow_style=False, indent=2)
            
            self._config_data = default_config
            self._parse_device_defaults()
            self._parse_devices()
            self._parse_monitoring()
            self._parse_logging()
            
            print(f"Created default configuration file: {self.config_path}")
            
        except Exception as e:
            raise ValueError(f"Error creating default configuration: {e}")
    
    def _parse_device_defaults(self):
        """Parse device default configuration from config data"""
        defaults_data = self._config_data.get('device_defaults', {})
        self._device_defaults = DeviceDefaults(
            port=defaults_data.get('port', 5555),
            process_name=defaults_data.get('process_name', 'com.nianticlabs.pokemongo'),
            binary_path=defaults_data.get('binary_path', '/data/local/tmp/newcosmog/com.nianticlabs.pokemongo'),
            working_directory=defaults_data.get('working_directory', '/data/local/tmp/newcosmog'),
            log_path=defaults_data.get('log_path', '/data/local/tmp/cosmog.log'),
            log_emission_enabled=defaults_data.get('log_emission_enabled', False),
            rotom_url=defaults_data.get('rotom_url', 'harris.lan:7072'),
            config_path=defaults_data.get('config_path', '/data/local/tmp/newcosmog/config.toml'),
            environment_vars=defaults_data.get('environment_vars', {'LD_LIBRARY_PATH': './lib'}),
            restart_on_failure=defaults_data.get('restart_on_failure', True),
            max_restart_attempts=defaults_data.get('max_restart_attempts', 3),
            restart_delay=defaults_data.get('restart_delay', 5)
        )
    
    def _parse_devices(self):
        """Parse device configurations from config data"""
        self._devices = []
        devices_data = self._config_data.get('devices', [])
        
        for device_data in devices_data:
            device = DeviceConfig(
                ip=device_data.get('ip'),
                port=device_data.get('port'),
                name=device_data.get('name'),
                binary_path=device_data.get('binary_path'),
                process_name=device_data.get('process_name'),
                working_directory=device_data.get('working_directory'),
                log_path=device_data.get('log_path'),
                log_emission_enabled=device_data.get('log_emission_enabled'),
                rotom_url=device_data.get('rotom_url'),
                config_path=device_data.get('config_path'),
                environment_vars=device_data.get('environment_vars'),
                restart_on_failure=device_data.get('restart_on_failure'),
                max_restart_attempts=device_data.get('max_restart_attempts'),
                restart_delay=device_data.get('restart_delay')
            )
            
            if not device.ip:
                raise ValueError("Device IP address is required")
            
            # Apply global defaults to the device
            device_with_defaults = device.apply_defaults(self._device_defaults)
            self._devices.append(device_with_defaults)
    
    def _parse_monitoring(self):
        """Parse monitoring configuration from config data"""
        monitoring_data = self._config_data.get('monitoring', {})
        self._monitoring = MonitoringConfig(
            interval=monitoring_data.get('interval', 30),
            timeout=monitoring_data.get('timeout', 10),
            retry_attempts=monitoring_data.get('retry_attempts', 3),
            retry_delay=monitoring_data.get('retry_delay', 5)
        )
    
    def _parse_logging(self):
        """Parse logging configuration from config data"""
        logging_data = self._config_data.get('logging', {})
        self._logging = LoggingConfig(
            level=logging_data.get('level', 'INFO'),
            format=logging_data.get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            file=logging_data.get('file', 'android_monitor.log'),
            max_size=logging_data.get('max_size', 10485760),
            backup_count=logging_data.get('backup_count', 5)
        )
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'monitoring.interval')"""
        keys = key.split('.')
        value = self._config_data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def get_devices(self) -> List[DeviceConfig]:
        """Get list of configured devices"""
        return self._devices
    
    def get_device(self, ip: str, port: int = 5555) -> Optional[DeviceConfig]:
        """Get specific device configuration by IP and port"""
        for device in self._devices:
            if device.ip == ip and device.port == port:
                return device
        return None
    
    def get_monitoring_config(self) -> MonitoringConfig:
        """Get monitoring configuration"""
        return self._monitoring
    
    def get_logging_config(self) -> LoggingConfig:
        """Get logging configuration"""
        return self._logging
    
    def get_device_defaults(self) -> DeviceDefaults:
        """Get device default configuration"""
        return self._device_defaults
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate devices
        if not self._devices:
            errors.append("No devices configured")
        
        for i, device in enumerate(self._devices):
            if not device.ip:
                errors.append(f"Device {i}: IP address is required")
            
            if not device.process_name:
                errors.append(f"Device {i}: Process name is required")
            
            if not device.binary_path:
                errors.append(f"Device {i}: Binary path is required")
        
        # Validate monitoring config
        if self._monitoring.interval <= 0:
            errors.append("Monitoring interval must be positive")
        
        if self._monitoring.timeout <= 0:
            errors.append("Monitoring timeout must be positive")
        
        return errors
    
    def reload(self):
        """Reload configuration from file"""
        self.load_config()
    
    def __str__(self) -> str:
        """String representation of configuration"""
        return f"Config(devices={len(self._devices)}, monitoring_interval={self._monitoring.interval}s)"
