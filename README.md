# DynDNS Client for OVH

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?logo=github)](https://github.com/cibrandocampo/ovh-dyndns-client)
[![Docker Hub](https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker)](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
[![GitHub release (latest by date)](https://img.shields.io/github/v/release/cibrandocampo/ovh-dyndns-client)](https://github.com/cibrandocampo/ovh-dyndns-client/releases)
[![Python](https://img.shields.io/badge/python-3.14-blue?logo=python)](https://www.python.org/)
[![Docker Pulls](https://img.shields.io/docker/pulls/cibrandocampo/ovh-dyndns-client)](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
[![codecov](https://codecov.io/gh/cibrandocampo/ovh-dyndns-client/graph/badge.svg)](https://codecov.io/gh/cibrandocampo/ovh-dyndns-client)

A robust client for keeping OVH domains pointing to a dynamic IP address, with a web interface for easy management.

![Dashboard Status](https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard-status.png)

## Features

- **Web Interface** — Manage hosts, view status and history from a browser
- **REST API** — Full-featured API with JWT authentication
- **SQLite Database** — Persistent storage, no external dependencies
- **Auto-updates** — Detects IP changes and updates DNS records automatically
- **Auto-retry** — Failed updates are retried on the next cycle
- **Docker-ready** — Multi-architecture support (amd64, arm64, arm/v7)

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

| Hosts | Settings |
|:---:|:---:|
| ![Hosts](https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard-hosts.png) | ![Settings](https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard-settings.png) |

- **Status** — Current public IP and per-host DNS update status
- **Hosts** — Add, edit, and delete OVH DynHost entries
- **History** — Full log of IP changes and update events
- **Settings** — Configure update interval and log level

## How It Works

1. Retrieves the current public IP using [ipify](https://www.ipify.org/)
2. Compares it with the IP stored in the local SQLite database
3. If it changed, updates all configured OVH DNS records via the DynHost API
4. Failed updates are tracked and retried automatically on the next cycle

## Quality

Every change goes through a CI pipeline (GitHub Actions) with no shortcuts:

- **Lint**: ruff check — enforces code style and catches common errors
- **Format**: ruff format — consistent formatting across the codebase
- **Tests**: pytest with a minimum **70% coverage** gate enforced in CI

The Codecov badge at the top of this page reflects the current state.

## Docker images

Pre-built multi-arch images (linux/amd64, linux/arm64, linux/arm/v7) are published to Docker Hub automatically.

| Tag | When |
|-----|------|
| `latest` | Every push to `main` |
| `stable` + `vX.Y.Z` | On GitHub release |

Images are also rebuilt weekly to pick up base-image and dependency security patches.

## Documentation

- [API Reference](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/API.md) — REST API endpoints and examples
- [Configuration](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/CONFIGURATION.md) — Environment variables and settings
- [Development](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md) — Architecture, dev setup, and Claude Code workflow

## Development

The development environment runs entirely inside Docker — no Python on the host. See [docs/DEVELOPMENT.md](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md) for the full setup, including how to run tests, linters, and install the pre-commit hook.

## Built with Claude Code

This project is developed with [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant. Custom skills and commands are provided in `.claude/` to maintain project conventions and support a structured dev workflow. See [docs/DEVELOPMENT.md](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md#claude-code) for details.

## Links

- [GitHub Repository](https://github.com/cibrandocampo/ovh-dyndns-client)
- [Docker Hub](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
- [OVH DynHost Documentation](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)

## Support

- **Issues**: [GitHub Issues](https://github.com/cibrandocampo/ovh-dyndns-client/issues)
- **Email**: [hello@cibran.es](mailto:hello@cibran.es)

## License

Released under the [MIT License](LICENSE).
