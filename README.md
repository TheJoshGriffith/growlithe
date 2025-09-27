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
houndour/
├── main.py                 # Main application entry point
├── config.py              # Configuration management
├── device_manager.py      # Android device connection management
├── process_manager.py     # Process lifecycle management
├── requirements.txt       # Python dependencies
├── Dockerfile            # Docker container configuration
├── docker-compose.yml    # Docker Compose configuration
├── config.yaml           # Application configuration (auto-generated)
├── run.sh               # Original bash script (for reference)
└── README.md            # This file
```

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd houndour
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

## Configuration Options

### Device Configuration

Each device in the `devices` array supports the following options:

- `ip`: Device IP address (required)
- `port`: ADB port (default: 5555)
- `name`: Human-readable device name
- `process_name`: Name of the process to monitor (required)
- `binary_path`: Full path to the executable binary (required)
- `working_directory`: Working directory for the process (required)
- `environment_vars`: Environment variables for the process
- `restart_on_failure`: Whether to restart the process if it fails (default: true)
- `max_restart_attempts`: Maximum number of restart attempts (default: 3)
- `restart_delay`: Delay between restart attempts in seconds (default: 5)

### Monitoring Configuration

- `interval`: Time between monitoring cycles in seconds (default: 30)
- `timeout`: Timeout for device operations in seconds (default: 10)
- `retry_attempts`: Number of retry attempts for failed operations (default: 3)
- `retry_delay`: Delay between retry attempts in seconds (default: 5)

### Logging Configuration

- `level`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `format`: Log message format
- `file`: Log file path
- `max_size`: Maximum log file size in bytes
- `backup_count`: Number of backup log files to keep

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
