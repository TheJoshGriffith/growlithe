# Android Device Monitor

A dockerized Python application for monitoring, restarting, and manipulating Android devices via ADB connections. This project provides a highly configurable and modular solution for managing multiple Android devices remotely.

## Features

- **Device Management**: Monitor multiple Android devices via ADB connections
- **Process Control**: Start, stop, and restart processes on Android devices
- **Automatic Recovery**: Automatic process restart on failure with configurable retry logic
- **Modular Design**: Object-oriented architecture with separate classes for different responsibilities
- **Dockerized**: Easy deployment with Docker and Docker Compose
- **Configurable**: YAML-based configuration for devices, processes, and monitoring settings
- **Logging**: Comprehensive logging with configurable levels and file rotation
- **Web Interface**: Optional web API for remote management (planned)

## Project Structure

```
growlithe/
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── device_manager.py      # Android device connection management
├── process_manager.py     # Process lifecycle management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose configuration
├── config.yaml           # Application configuration (auto-generated)
├── config.yaml.example   # Example configuration file
├── run.sh               # Original bash script (for reference)
└── README.md            # This file
```

## Quick Start

### 1. Clone and Setup

```bash
git clone git@github.com:TheJoshGriffith/growlithe.git
cd growlithe
```

### 2. Configuration

The application will automatically create a default `config.yaml` file on first run. You can customize it for your devices:

```yaml
devices:
  - ip: "10.0.1.50"
    port: 5555
    name: "Device 1"
    process_name: "com.nianticlabs.pokemongo"
    binary_path: "/data/local/tmp/newcosmog/com.nianticlabs.pokemongo"
    working_directory: "/data/local/tmp/newcosmog"
    environment_vars:
      LD_LIBRARY_PATH: "./lib"
    restart_on_failure: true
    max_restart_attempts: 3
    restart_delay: 5

monitoring:
  interval: 30
  timeout: 10
  retry_attempts: 3
  retry_delay: 5

logging:
  level: "INFO"
  format: "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  file: "android_monitor.log"
```

### 3. Docker Deployment

#### Option A: Run from GitHub Container Registry (Recommended)

```bash
# Pull the latest image from GHCR
docker pull ghcr.io/thejoshgriffith/growlithe:latest

# Create your configuration file
cp config.yaml.example config.yaml
# Edit config.yaml with your device IPs and settings

# Run the container with your config
docker run -d \
  --name android-monitor \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  ghcr.io/thejoshgriffith/growlithe:latest

# View logs
docker logs -f android-monitor

# Stop the service
docker stop android-monitor && docker rm android-monitor
```

#### Option B: Build and run with Docker Compose

```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f android-monitor

# Stop the service
docker-compose down
```

### 4. Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run once (for testing)
python main.py --once

# Run continuously
python main.py

# Run with verbose logging
python main.py --verbose
```

## Running from GitHub Container Registry

The easiest way to get started is using the pre-built Docker image from GitHub Container Registry (GHCR). This eliminates the need to build the image locally.

### Quick Start with GHCR

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
  -v $(pwd)/logs:/app/logs \
  ghcr.io/thejoshgriffith/growlithe:latest
```

### GHCR Image Tags

- `ghcr.io/thejoshgriffith/growlithe:latest` - Latest stable release
- `ghcr.io/thejoshgriffith/growlithe:main` - Latest from main branch
- `ghcr.io/thejoshgriffith/growlithe:v1.0.0` - Specific version (when available)

### Configuration File Setup

The container expects a `config.yaml` file to be mounted. Use the provided example:

```bash
# Copy the example configuration
cp config.yaml.example config.yaml

# Edit with your device details
nano config.yaml  # or your preferred editor
```

**Required changes in config.yaml:**
- Update device IP addresses in the `devices` section
- Adjust any paths, ports, or process names as needed
- Configure monitoring intervals and timeouts

### Docker Run Options

```bash
# Basic run
docker run -d \
  --name android-monitor \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  ghcr.io/thejoshgriffith/growlithe:latest

# With log persistence and auto-restart
docker run -d \
  --name android-monitor \
  --restart unless-stopped \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -v $(pwd)/logs:/app/logs \
  ghcr.io/thejoshgriffith/growlithe:latest

# With custom environment variables
docker run -d \
  --name android-monitor \
  --network host \
  -v $(pwd)/config.yaml:/app/config.yaml:ro \
  -e PYTHONUNBUFFERED=1 \
  -e TZ=UTC \
  ghcr.io/thejoshgriffith/growlithe:latest
```

### Container Management

```bash
# View logs
docker logs -f android-monitor

# Check container status
docker ps

# Stop the container
docker stop android-monitor

# Remove the container
docker rm android-monitor

# Update to latest version
docker pull ghcr.io/thejoshgriffith/growlithe:latest
docker stop android-monitor
docker rm android-monitor
# Then run the new container with the same command
```

## Configuration Options

The application uses a YAML configuration file (`config.yaml`) that supports multiple configuration sections. The configuration is automatically created on first run with sensible defaults.

### Configuration Structure

```yaml
device_defaults:     # Global defaults for all devices
devices:            # Individual device configurations
monitoring:         # Monitoring behavior settings
logging:           # Logging configuration
adb:              # ADB-specific settings
web:              # Web interface settings (optional)
```

### Device Defaults (`device_defaults`)

Global default values applied to all devices unless overridden:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `port` | int | `5555` | Default ADB port for device connections |
| `process_name` | string | `"com.nianticlabs.pokemongo"` | Default process name to monitor |
| `binary_path` | string | `"/data/local/tmp/newcosmog/com.nianticlabs.pokemongo"` | Default path to executable binary |
| `working_directory` | string | `"/data/local/tmp/newcosmog"` | Default working directory for processes |
| `log_path` | string | `"/data/local/tmp/cosmog.log"` | Default log file path on device |
| `log_emission_enabled` | bool | `false` | Whether to enable log emission from device |
| `rotom_url` | string | `"harris.lan:7072"` | Default Rotom client URL |
| `config_path` | string | `"/data/local/tmp/newcosmog/config.toml"` | Default config file path on device |
| `environment_vars` | dict | `{"LD_LIBRARY_PATH": "./lib"}` | Default environment variables |
| `restart_on_failure` | bool | `true` | Whether to restart processes on failure |
| `max_restart_attempts` | int | `3` | Maximum restart attempts before giving up |
| `restart_delay` | int | `5` | Delay between restart attempts (seconds) |

### Device Configuration (`devices`)

Individual device configurations. Each device inherits from `device_defaults` but can override any setting:

| Option | Type | Required | Description |
|--------|------|----------|-------------|
| `ip` | string | ✅ | Device IP address |
| `port` | int | ❌ | ADB port (inherits from defaults) |
| `name` | string | ❌ | Human-readable device name |
| `process_name` | string | ❌ | Process name to monitor (inherits from defaults) |
| `binary_path` | string | ❌ | Path to executable binary (inherits from defaults) |
| `working_directory` | string | ❌ | Working directory (inherits from defaults) |
| `log_path` | string | ❌ | Log file path on device (inherits from defaults) |
| `log_emission_enabled` | bool | ❌ | Enable log emission (inherits from defaults) |
| `rotom_url` | string | ❌ | Rotom client URL (inherits from defaults) |
| `config_path` | string | ❌ | Config file path on device (inherits from defaults) |
| `environment_vars` | dict | ❌ | Environment variables (inherits from defaults) |
| `restart_on_failure` | bool | ❌ | Restart on failure (inherits from defaults) |
| `max_restart_attempts` | int | ❌ | Max restart attempts (inherits from defaults) |
| `restart_delay` | int | ❌ | Restart delay (inherits from defaults) |

### Monitoring Configuration (`monitoring`)

Controls the monitoring behavior and timing:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `interval` | int | `30` | Time between monitoring cycles (seconds) |
| `timeout` | int | `10` | Timeout for device operations (seconds) |
| `retry_attempts` | int | `3` | Number of retry attempts for failed operations |
| `retry_delay` | int | `5` | Delay between retry attempts (seconds) |

### Logging Configuration (`logging`)

Controls application logging behavior:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `level` | string | `"INFO"` | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `format` | string | `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"` | Log message format |
| `file` | string | `"android_monitor.log"` | Log file path |
| `max_size` | int | `10485760` | Maximum log file size (bytes, 10MB) |
| `backup_count` | int | `5` | Number of backup log files to keep |

### ADB Configuration (`adb`)

ADB-specific settings:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `path` | string | `"adb"` | Path to ADB executable |
| `connect_timeout` | int | `10` | Connection timeout (seconds) |
| `command_timeout` | int | `30` | Command execution timeout (seconds) |

### Web Interface Configuration (`web`)

Optional web interface settings:

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `enabled` | bool | `false` | Enable web interface |
| `host` | string | `"0.0.0.0"` | Web interface host |
| `port` | int | `8080` | Web interface port |
| `api_key` | string | `null` | API key for authentication (optional) |

### Configuration Examples

#### Minimal Configuration
```yaml
devices:
  - ip: "10.0.1.50"
  - ip: "10.0.1.52"
```

#### Advanced Configuration
```yaml
device_defaults:
  port: 5555
  process_name: "com.nianticlabs.pokemongo"
  binary_path: "/data/local/tmp/newcosmog/com.nianticlabs.pokemongo"
  working_directory: "/data/local/tmp/newcosmog"
  environment_vars:
    LD_LIBRARY_PATH: "./lib"
    DEBUG: "1"
  restart_on_failure: true
  max_restart_attempts: 5
  restart_delay: 10

devices:
  - ip: "10.0.1.50"
    name: "Primary Device"
    port: 5555
    restart_delay: 3  # Override default
    
  - ip: "10.0.1.52"
    name: "Secondary Device"
    port: 5556
    process_name: "com.custom.app"  # Different process
    binary_path: "/data/local/tmp/custom/app"
    working_directory: "/data/local/tmp/custom"
    environment_vars:
      LD_LIBRARY_PATH: "./lib"
      CUSTOM_VAR: "value"
    restart_on_failure: false  # Disable auto-restart

monitoring:
  interval: 15  # Check every 15 seconds
  timeout: 20   # Longer timeout
  retry_attempts: 5
  retry_delay: 3

logging:
  level: "DEBUG"
  file: "detailed_monitor.log"
  max_size: 20971520  # 20MB
  backup_count: 10

adb:
  path: "/usr/local/bin/adb"
  connect_timeout: 15
  command_timeout: 45

web:
  enabled: true
  host: "0.0.0.0"
  port: 8080
  api_key: "your-secret-api-key"
```

#### Mixed Configuration (Some devices with defaults, others customized)
```yaml
device_defaults:
  port: 5555
  process_name: "com.nianticlabs.pokemongo"
  binary_path: "/data/local/tmp/newcosmog/com.nianticlabs.pokemongo"
  working_directory: "/data/local/tmp/newcosmog"
  restart_on_failure: true

devices:
  # Uses all defaults
  - ip: "10.0.1.50"
  
  # Custom port only
  - ip: "10.0.1.51"
    port: 5556
  
  # Completely custom configuration
  - ip: "10.0.1.52"
    name: "Custom Device"
    process_name: "com.custom.app"
    binary_path: "/data/local/tmp/custom/app"
    working_directory: "/data/local/tmp/custom"
    restart_on_failure: false
```

## Usage Examples

### Command Line Options

```bash
# Run with custom config file
python main.py --config /path/to/config.yaml

# Run once instead of continuous monitoring
python main.py --once

# Enable verbose logging
python main.py --verbose

# Combine options
python main.py --config custom.yaml --once --verbose
```

### Docker Commands

```bash
# Build the image
docker build -t android-monitor .

# Run with custom config
docker run -v $(pwd)/config.yaml:/app/config.yaml android-monitor

# Run in background
docker run -d --name android-monitor android-monitor

# View logs
docker logs -f android-monitor

# Stop and remove
docker stop android-monitor && docker rm android-monitor
```

## Architecture

### Core Classes

1. **AndroidMonitor**: Main application class that orchestrates monitoring
2. **Config**: Configuration management with YAML support
3. **DeviceManager**: Handles ADB connections and device state
4. **ProcessManager**: Manages process lifecycle and restart logic

### Key Features

- **Asynchronous Operations**: Uses asyncio for non-blocking device operations
- **Error Handling**: Comprehensive error handling with retry logic
- **Status Tracking**: Tracks device and process status with detailed information
- **Graceful Shutdown**: Handles SIGINT/SIGTERM for clean shutdown
- **Resource Management**: Proper cleanup of connections and resources

## Prerequisites

### System Requirements

- Python 3.11+
- ADB (Android Debug Bridge) installed
- Docker and Docker Compose (for containerized deployment)
- Network access to Android devices

### Android Device Setup

1. Enable Developer Options on your Android devices
2. Enable USB Debugging
3. Connect devices to the same network
4. Enable ADB over WiFi (or use USB connection)
5. Ensure devices are accessible via ADB on the specified ports

## Troubleshooting

### Common Issues

1. **ADB Connection Failed**
   - Check if ADB is installed and in PATH
   - Verify device IP addresses and ports
   - Ensure devices have ADB over WiFi enabled

2. **Process Not Starting**
   - Verify binary path exists on the device
   - Check working directory permissions
   - Ensure environment variables are correct

3. **Permission Denied**
   - Ensure the application has proper permissions
   - Check if devices are rooted (required for some operations)

### Debug Mode

Enable debug logging to troubleshoot issues:

```bash
python main.py --verbose
```

Or set logging level to DEBUG in config.yaml:

```yaml
logging:
  level: "DEBUG"
```

## Development

### Adding New Features

1. Create new classes in separate files
2. Follow the existing architecture patterns
3. Add configuration options to `config.py`
4. Update documentation

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=.

# Type checking
mypy .
```

## License

[Add your license information here]

## Contributing

[Add contribution guidelines here]

## Support

[Add support information here]
