# DynDNS Client for OVH

This client keeps an OVH domain pointing to a dynamic IP.

The process is simple and consists of three steps:
1. The **ipify** library is used to get the current public IP.
2. If the obtained IP is different from the last one registered with OVH, the update process is triggered.
3. The OVH API is called for each configured domain to update its IP.

## Quick Reference Information:
- Official OVH documentation: [OVH Dynhost Docs](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)
- Official IPIFY documentation: [Python-IPIFY GitHub](https://github.com/rdegges/python-ipify)

---

## How to Use This Project

To use this project, follow these steps:

1. **Configure the hosts** that you want to keep updated with your OVH account.
2. **Deploy the service** using Docker or manually.

### Host Configuration

The first and most important step is to configure the hosts that need to be updated. To do so, you should create or fill in the example JSON configuration file:

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

📌 **Note:** The example file is available at: `docs/hosts_example.json`.

### Service Deployment

There is a stable version of the OVH DynDNS Client published on DockerHub (https://hub.docker.com/repository/docker/cibrandocampo/ovh-dyndns-client), so it's as easy as using that image with the available Docker Compose file found in `/docs`:

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:${DOCKER_OVH_VERSION:-stable}
    container_name: "${PROJECT_NAME:-dyndns-client}"
    restart: always
    env_file:
      - .env
    volumes:
      - ${HOSTS_CONFIG_FILE_PATH}:/app/hosts.json
```

With the correct configuration (according to your file paths) in the `.env` file (also available in `/docs`):

```ini
# Project
PROJECT_NAME=ovh-dyndns

# Docker version
DOCKER_OVH_VERSION=2.0.0

# General config
HOSTS_CONFIG_FILE_PATH=/volume1/docker/network/dyndns/volumes/hosts.json
UPDATE_INTERVAL=300

# Logger
LOGGER_NAME=ovh-dydns
LOGGER_LEVEL=INFO
```

### List of Available Environment Variables:

| Variable | Default Value | Description |
|----------|---------------|-------------|
| `HOSTS_CONFIG_FILE_PATH` | `config/hosts.json` | Path to the JSON configuration file containing the host details. |
| `UPDATE_INTERVAL` | `300` (seconds) | Interval in seconds to check and update the IP. |
| `LOGGER_NAME` | `ovh-dydns` | Name of the logger for the application. |
| `LOGGER_LEVEL` | `INFO` | Log level. Can be set to `DEBUG`, `INFO`, `WARNING`, `ERROR`, or `CRITICAL`. |

---

## Need Help?

If you need additional support, feel free to reach out via email: [hello@cibran.es](mailto:hello@cibran.es)

## License

This project is licensed under the **GNU General Public License**.
