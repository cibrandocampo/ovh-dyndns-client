# DynDNS Client for OVH

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/cibrandocampo/ovh-dyndns-client)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker)](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cibrandocampo/ovh-dyndns-client)](https://github.com/cibrandocampo/ovh-dyndns-client/releases)
[![Python](https://img.shields.io/badge/python-3.14-blue?logo=python)](https://www.python.org/)
[![Docker Pulls](https://img.shields.io/docker/pulls/cibrandocampo/ovh-dyndns-client)](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
[![License](https://img.shields.io/badge/License-GPL%20v3.0-green.svg)](LICENSE)

A robust and efficient client for keeping OVH domains pointing to a dynamic IP address.

This client automatically maintains your OVH domains pointing to your current public IP, even when it changes. It uses the Singleton pattern to optimize performance and avoid unnecessary updates.

## Features

- **Automatic updates**: Detects IP changes and updates only when necessary
- **High performance**: Singleton pattern to avoid unnecessary reinitializations
- **Docker-ready**: Official image available on DockerHub with multi-architecture support (amd64, arm64/v8, arm/v7)
- **Complete logging**: Configurable and detailed logging system
- **Efficient**: Only updates when the IP actually changes
- **Robust**: Error handling and automatic recovery

## Quick Start

### Docker Image

Pre-built images are available on [Docker Hub](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client). For production use, two tags are recommended:

- **`latest`**: Most up-to-date version passing unit tests
- **`stable`**: Latest version passing both unit and integration tests (recommended for production)

Version-specific tags are also available (e.g., `2.0.0`).

### Setup

1. **Create `docker-compose.yaml`:**

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:${DOCKER_OVH_VERSION:-stable}
    container_name: "${PROJECT_NAME:-ovh-dyndns-client}"
    restart: always
    init: true
    env_file:
      - .env
    volumes:
      - ${HOSTS_CONFIG_FILE_PATH}:/app/hosts.json
```

2. **Create `.env` file:**

```ini
PROJECT_NAME=ovh-dyndns-client
DOCKER_OVH_VERSION=stable
HOSTS_CONFIG_FILE_PATH=/path/to/hosts.json
UPDATE_INTERVAL=600
LOGGER_LEVEL=INFO
```

Available environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PROJECT_NAME` | `ovh-dyndns-client` | Container name |
| `DOCKER_OVH_VERSION` | `stable` | Docker image version |
| `HOSTS_CONFIG_FILE_PATH` | `/app/hosts.json` | Path to hosts JSON file |
| `UPDATE_INTERVAL` | `300` | Check interval in seconds |
| `LOGGER_NAME` | `ovh-dydns` | Logger name |
| `LOGGER_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

3. **Create `hosts.json` file:**

```json
[
    {
        "hostname": "example.es",
        "username": "example-user",
        "password": "example-password"
    },
    {
        "hostname": "example2.es", 
        "username": "example2-user",
        "password": "example2-password"
    }
]
```

4. **Run:**

```bash
docker compose up -d
```

## How It Works

1. Retrieves current public IP using **ipify**
2. Compares with last registered IP
3. Updates OVH DNS records only if IP changed

## Monitoring and Logs

### Normal Operation Logs

```
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Executing DNS update controller
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Starting DNS update process
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Retrieved public IP: 83.34.148.172
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | IP unchanged, skipping update
2025-10-24T12:01:35+0000 (ovh-dydns) INFO | DNS update completed successfully
```

### IP Change Logs

```
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Executing DNS update controller
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Starting DNS update process
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | Retrieved public IP: 83.34.148.173
2025-10-24T12:01:32+0000 (ovh-dydns) INFO | IP changed, updating hosts
2025-10-24T12:01:33+0000 (ovh-dydns) INFO | example.es | Authenticating as example-user
2025-10-24T12:01:33+0000 (ovh-dydns) INFO | example.es | Updating IP
2025-10-24T12:01:33+0000 (ovh-dydns) INFO | example.es | Update response: 200 good 83.34.148.173
2025-10-24T12:01:35+0000 (ovh-dydns) INFO | DNS update completed successfully
```

## Development

### Development Environment

For development, this project includes a complete Docker-based development environment with hot reload, debugging support, and automated testing tools.

**Quick Start:**
```bash
cd dev/
make build
make up
make shell
```

**Available Commands:**
- `make test` - Run tests
- `make lint` - Code quality checks
- `make format` - Format code
- `make logs` - View logs
- `make clean` - Clean up

For detailed development instructions, see the [Development README](dev/README.md).

### Project Structure

```
src/
├── application/          # Application logic
│   └── controller.py     # Main controller
├── domain/               # Domain models
│   └── hostconfig.py     # Host configuration
├── infrastructure/       # Infrastructure
│   ├── clients/         # External clients
│   │   ├── ipify_client.py
│   │   └── ovh_client.py
│   ├── config.py        # Configuration (Singleton)
│   └── logger.py        # Logging system
├── test/                # Unit tests
└── main.py             # Entry point
```

### Running Tests

```bash
# Using development environment
cd dev/
make test

# Or run directly (requires local Python environment)
python -m pytest src/test/ -v
```

### Test Coverage

The project maintains high test coverage to ensure code quality and reliability. Current coverage status:

| Module | Coverage | Notes |
|--------|----------|-------|
| `application/controller.py` | 100% | - |
| `infrastructure/clients/ipify_client.py` | 100% | - |
| `infrastructure/clients/ovh_client.py` | 100% | - |
| `infrastructure/config.py` | 96% | - |
| `infrastructure/logger.py` | 89% | - |
| `domain/hostconfig.py` | 88% | - |
| `main.py` | 0% | Entry point |

**Overall coverage: 93%**

Tests are automatically executed in CI/CD pipelines before building Docker images to ensure code quality.

### Architecture

Uses Singleton pattern for `Config` class to maintain IP state between scheduler executions and avoid unnecessary reinitializations.

## Links

- **GitHub Repository**: [github.com/cibrandocampo/ovh-dyndns-client](https://github.com/cibrandocampo/ovh-dyndns-client)
- **Docker Hub Image**: [hub.docker.com/r/cibrandocampo/ovh-dyndns-client](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)

## References

- [OVH Dynhost Documentation](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)
- [Python-IPIFY](https://github.com/rdegges/python-ipify)

## Dependencies

This project is built on top of open source libraries:

- **[ipify](https://github.com/rdegges/python-ipify)**: For retrieving the current public IP address
- **[requests](https://requests.readthedocs.io/)**: For making HTTP requests to the OVH API
- **[pydantic](https://pydantic-docs.helpmanual.io/)**: For data validation and settings management
- **[schedule](https://schedule.readthedocs.io/)**: For periodic task execution

## Support

- **Email**: [hello@cibran.es](mailto:hello@cibran.es)
- **Issues**: Open an issue in the repository

## License

Licensed under **GNU General Public License v3.0**. See [LICENSE](LICENSE) for details.
