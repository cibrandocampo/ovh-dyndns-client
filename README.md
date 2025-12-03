# DynDNS Client for OVH

A robust and efficient client for keeping OVH domains pointing to a dynamic IP address.

This client automatically maintains your OVH domains pointing to your current public IP, even when it changes. It uses the Singleton pattern to optimize performance and avoid unnecessary updates.

## Features

- **Automatic updates**: Detects IP changes and updates only when necessary
- **High performance**: Singleton pattern to avoid unnecessary reinitializations
- **Docker-ready**: Official image available on DockerHub
- **Complete logging**: Configurable and detailed logging system
- **Efficient**: Only updates when the IP actually changes
- **Robust**: Error handling and automatic recovery

## How It Works

The process is simple and consists of three steps:

1. The **ipify** library is used to get the current public IP.
2. If the obtained IP is different from the last one registered with OVH, the update process is triggered.
3. The OVH API is called for each configured domain to update its IP.

## Quick Reference Information

- Official OVH documentation: [OVH Dynhost Docs](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)
- Official IPIFY documentation: [Python-IPIFY GitHub](https://github.com/rdegges/python-ipify)

## Installation and Usage

### 1. Host Configuration

Create a JSON file with your domain configuration:

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

### 2. Docker Compose Deployment

Create a `docker-compose.yaml` file:

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

### 3. Environment Variables

Create a `.env` file with the following configuration:

```ini
# Project
PROJECT_NAME=ovh-dyndns-client

# Docker version
DOCKER_OVH_VERSION=stable

# General config
HOSTS_CONFIG_FILE_PATH=/volume1/docker/network/dyndns/volumes/hosts.json
UPDATE_INTERVAL=300

# Logger
LOGGER_NAME=ovh-dydns
LOGGER_LEVEL=INFO
```

### 4. Run

```bash
docker-compose up -d
```

## Advanced Configuration

### Available Environment Variables

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `PROJECT_NAME` | `ovh-dyndns-client` | Container name for the application |
| `DOCKER_OVH_VERSION` | `stable` | Docker image version to use |
| `HOSTS_CONFIG_FILE_PATH` | `/app/hosts.json` | Path to the JSON configuration file containing the host details |
| `UPDATE_INTERVAL` | `300` (seconds) | Interval in seconds to check and update the IP |
| `LOGGER_NAME` | `ovh-dydns` | Name of the logger for the application |
| `LOGGER_LEVEL` | `INFO` | Log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

### Complete Configuration Example

```ini
# Project configuration
PROJECT_NAME=my-dyndns-client
DOCKER_OVH_VERSION=2.0.0

# General configuration
HOSTS_CONFIG_FILE_PATH=/home/user/dyndns/hosts.json
UPDATE_INTERVAL=600

# Logger configuration
LOGGER_NAME=my-dyndns
LOGGER_LEVEL=DEBUG
```

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

### Singleton Pattern

The project uses the Singleton pattern for the `Config` class, which ensures:

- **Persistent state**: IP is maintained between scheduler executions
- **Efficiency**: Avoids unnecessary reinitializations
- **Consistency**: Single source of truth for configuration

## Dependencies

This project is built on top of open source libraries:

- **[ipify](https://github.com/rdegges/python-ipify)**: For retrieving the current public IP address
- **[requests](https://requests.readthedocs.io/)**: For making HTTP requests to the OVH API
- **[pydantic](https://pydantic-docs.helpmanual.io/)**: For data validation and settings management
- **[schedule](https://schedule.readthedocs.io/)**: For periodic task execution

## References

- **Official OVH documentation**: [OVH Dynhost Docs](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)
- **IPIFY documentation**: [Python-IPIFY GitHub](https://github.com/rdegges/python-ipify)
- **DockerHub**: [cibrandocampo/ovh-dyndns-client](https://hub.docker.com/repository/docker/cibrandocampo/ovh-dyndns-client)

## Support

If you need additional support, feel free to reach out:

- **Email**: [hello@cibran.es](mailto:hello@cibran.es)
- **Issues**: Report problems in the repository

## License

This project is licensed under the **GNU General Public License v3.0**.

This means:
- ✅ **Free to use**: Anyone can use this software for any purpose
- ✅ **Open source**: Source code must remain open and accessible
- ✅ **Share improvements**: Any modifications or improvements must be published under the same license
- ✅ **Commercial use**: Can be used commercially, but derivative works must also be open source

For more details, see the [LICENSE](LICENSE) file or visit [GNU GPL v3](https://www.gnu.org/licenses/gpl-3.0.html).

---

<div align="center">
  <strong>Made with ❤️ by <a href="https://cibran.es">Cibrán Docampo</a></strong>
</div>