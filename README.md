# Android Device Monitor

A dockerized Python application for monitoring and managing Android devices via ADB connections. Automatically restarts processes on failure with configurable retry logic.

## Features

- Monitor multiple Android devices via ADB
- Automatic process restart on failure
- YAML-based configuration
- Docker deployment ready
- Comprehensive logging


## Quick Start

### Run from GitHub Container Registry (Recommended)

```bash
# 1. Pull the latest image
docker pull ghcr.io/thejoshgriffith/growlithe:latest

# 2. Create your configuration
cp config.yaml.example config.yaml
# Edit config.yaml with your device IPs

# 3. Run the container
docker run -d \
  --name android-monitor \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ghcr.io/thejoshgriffith/growlithe:latest

# View logs
docker logs -f android-monitor
```

### Alternative: Docker Compose

```bash
# Clone and run with Docker Compose
git clone git@github.com:TheJoshGriffith/growlithe.git
cd growlithe
docker-compose up -d
```


## Configuration

The application uses a YAML configuration file (`config.yaml`) with global defaults and per-device overrides.

### Basic Configuration

```yaml
# Global defaults for all devices
device_defaults:
  port: 5555
  process_name: com.nianticlabs.pokemongo
  binary_path: /data/local/tmp/newcosmog/com.nianticlabs.pokemongo
  working_directory: /data/local/tmp/newcosmog
  restart_on_failure: true
  max_restart_attempts: 3
  restart_delay: 5

# Individual devices (only IP required, others inherit from defaults)
devices:
  - ip: 10.0.1.50
  - ip: 10.0.1.51
    port: 5556  # Override default port
    name: "Secondary Device"

# Monitoring settings
monitoring:
  interval: 30  # Check every 30 seconds
  timeout: 10   # 10 second timeout for operations
  retry_attempts: 3
  retry_delay: 5

# Logging
logging:
  level: INFO
  file: android_monitor.log
```

### Key Configuration Options

**Device Settings:**
- `ip` - Device IP address (required)
- `port` - ADB port (default: 5555)
- `process_name` - Process to monitor
- `binary_path` - Path to executable on device
- `working_directory` - Process working directory
- `restart_on_failure` - Auto-restart on failure (default: true)
- `max_restart_attempts` - Max restart attempts (default: 3)
- `restart_delay` - Delay between restarts in seconds (default: 5)
- `log_emission_enabled` - Will take all logs from MITM and emit them to stdout, prefixed by device IP (default: false)

**Monitoring Settings:**
- `interval` - Check interval in seconds (default: 30)
- `timeout` - Operation timeout in seconds (default: 10)
- `retry_attempts` - Retry attempts for failed operations (default: 3)

**Logging Settings:**
- `level` - Log level: DEBUG, INFO, WARNING, ERROR (default: INFO)
- `file` - Log file path (default: android_monitor.log)

## Prerequisites

- ADB (Android Debug Bridge) installed
- Docker (for containerized deployment)
- Network access to Android devices
- Android devices with Developer Options and USB Debugging enabled

## Troubleshooting

**ADB Connection Failed:**
- Verify device IP addresses and ports
- Ensure devices have ADB over WiFi enabled
- Check if ADB is installed and accessible

**Process Not Starting:**
- Verify binary path exists on the device
- Check working directory permissions
- Ensure environment variables are correct

**Enable Debug Logging:**
```yaml
logging:
  level: DEBUG
```
