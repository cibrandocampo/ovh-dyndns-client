# DynDNS Client for OVH

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/cibrandocampo/ovh-dyndns-client)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker)](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cibrandocampo/ovh-dyndns-client)](https://github.com/cibrandocampo/ovh-dyndns-client/releases)
[![Python](https://img.shields.io/badge/python-3.14-blue?logo=python)](https://www.python.org/)
[![Docker Pulls](https://img.shields.io/docker/pulls/cibrandocampo/ovh-dyndns-client)](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
[![codecov](https://codecov.io/gh/cibrandocampo/ovh-dyndns-client/graph/badge.svg)](https://codecov.io/gh/cibrandocampo/ovh-dyndns-client)

A robust client for keeping OVH domains pointing to a dynamic IP address, with a web interface for easy management.

![Dashboard](https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard.png)

## Features

- **Web Interface** - Manage hosts, view status and history
- **REST API** - Full-featured API with JWT authentication
- **SQLite Database** - Persistent storage, no external dependencies
- **Auto-updates** - Detects IP changes and updates DNS automatically
- **Auto-retry** - Failed updates are retried on the next cycle
- **Docker-ready** - Multi-architecture support (amd64, arm64, arm/v7)

## Quick Start

1. **Create `docker-compose.yaml`:**

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:stable
    container_name: ovh-dyndns-client
    restart: always
    environment:
      - JWT_SECRET=your-secret-key-min-32-chars-long!
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
```

2. **Run:**

```bash
docker compose up -d
```

3. **Access:** Open http://localhost:8000

Default credentials: `admin` / `admin` (password change required on first login)

## Web Interface

- **Status** - Current IP and host status
- **Hosts** - Add, edit, delete DNS hosts
- **History** - View all IP changes and updates
- **Settings** - Configure update interval and log level

## Documentation

- [API Reference](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/API.md) - REST API endpoints and examples
- [Configuration](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/CONFIGURATION.md) - Environment variables and settings
- [Development](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md) - Architecture and contribution guide

## How It Works

1. Retrieves current public IP using [ipify](https://www.ipify.org/)
2. Compares with stored IP in SQLite database
3. If changed, updates all OVH DNS records via DynHost API
4. Failed updates are tracked and retried automatically

## Links

- [GitHub Repository](https://github.com/cibrandocampo/ovh-dyndns-client)
- [Docker Hub](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
- [OVH DynHost Documentation](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)

## Support

- **Issues**: [GitHub Issues](https://github.com/cibrandocampo/ovh-dyndns-client/issues)
- **Email**: [hello@cibran.es](mailto:hello@cibran.es)

## License

[MIT License](LICENSE)
