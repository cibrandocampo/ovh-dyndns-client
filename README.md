# DynDNS Client for OVH

<p align="center">
  <a href="https://github.com/cibrandocampo/ovh-dyndns-client"><img src="https://img.shields.io/badge/GitHub-Repository-blue?logo=github" alt="GitHub"/></a>
  <a href="https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client"><img src="https://img.shields.io/badge/Docker%20Hub-Image-blue?logo=docker" alt="Docker Hub"/></a>
  <a href="https://github.com/cibrandocampo/ovh-dyndns-client/releases"><img src="https://img.shields.io/github/v/release/cibrandocampo/ovh-dyndns-client" alt="GitHub release"/></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/python-3.14-blue?logo=python" alt="Python"/></a>
  <a href="https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client"><img src="https://img.shields.io/docker/pulls/cibrandocampo/ovh-dyndns-client" alt="Docker Pulls"/></a>
  <a href="https://codecov.io/gh/cibrandocampo/ovh-dyndns-client"><img src="https://codecov.io/gh/cibrandocampo/ovh-dyndns-client/graph/badge.svg" alt="codecov"/></a>
  <a href="https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License MIT"/></a>
</p>

*Your IP changes. Your domains shouldn't.* Point your OVH domains to a dynamic IP and forget about it — one container, no external dependencies, your server, your rules.

![Dashboard Status](https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard-status.png)

---

> [!NOTE]
> **Upgrading from v4.3.0 or earlier?** First boot of the new image
> auto-generates persisted secrets under `./data` and encrypts your OVH
> host passwords at rest. Zero-touch — `docker compose pull && up -d`
> is enough. Heads-up on the new behaviours (server-side forced password
> change, rate limiting on `/api/auth/*`, critical `data/` directory):
>
> → **[Upgrade guide](docs/CONFIGURATION.md#migrating-from-a-previous-release)**

---

## A closer look — How it works?

### Hosts — one entry per domain record

<img src="https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard-hosts.png" align="left" width="380" alt="Hosts management screen with a list of configured OVH DynHost entries and their credentials"/>

Each host corresponds to a DynHost entry in your OVH control panel. Add as many as you need — subdomains, multiple domains, different zones — each with its own OVH credentials. The client updates them all in parallel on every IP change.

Creating a host takes seconds: hostname, OVH username, and password. That is all the client needs to keep the record in sync. Hosts can be edited or removed at any time without restarting the service.

<br clear="left"/>

---

### Settings — tune the behaviour without touching a config file

<img src="https://raw.githubusercontent.com/cibrandocampo/ovh-dyndns-client/main/docs/dashboard-settings.png" align="right" width="380" alt="Settings screen with update interval selector and log level dropdown"/>

The check interval and log verbosity can be adjusted from the web interface at any time — no restart, no editing environment variables. Lower the interval if your IP changes frequently; raise it if you want to reduce external API calls.

Log level controls how much detail appears in the container logs, useful when troubleshooting a failed update or verifying that a specific host was reached.

<br clear="right"/>

---

## Features

- **Web Interface** — Manage hosts, view status and history from a browser
- **REST API** — Full-featured API with JWT authentication
- **SQLite Database** — Persistent storage, no external dependencies
- **Auto-updates** — Detects IP changes and updates DNS records automatically
- **Auto-retry** — Failed updates are retried on the next cycle
- **Docker-ready** — Multi-architecture support (amd64, arm64, arm/v7)

---

## Quick Start

1. **Create `docker-compose.yaml`:**

```yaml
services:
  ovh-dyndns-client:
    image: cibrandocampo/ovh-dyndns-client:stable
    container_name: ovh-dyndns-client
    restart: always
    # JWT_SECRET and ENCRYPTION_KEY are auto-generated under ./data on first
    # start. Override only if you need fixed values across deployments — see
    # docs/CONFIGURATION.md.
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

---

## Quality

Every change goes through a CI pipeline (GitHub Actions) with no shortcuts:

- **Lint**: ruff check — enforces code style and catches common errors
- **Format**: ruff format — consistent formatting across the codebase
- **Tests**: pytest with a minimum **90% coverage** gate enforced in CI

The Codecov badge at the top of this page reflects the current state.

---

## Docker images

Pre-built multi-arch images (linux/amd64, linux/arm64, linux/arm/v7) are published to Docker Hub automatically.

| Tag | When |
|-----|------|
| `latest` | Every push to `main` |
| `stable` + `vX.Y.Z` | On GitHub release |

Images are also rebuilt weekly to pick up base-image and dependency security patches.

---

## Documentation

- [API Reference](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/API.md) — REST API endpoints and examples
- [Configuration](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/CONFIGURATION.md) — Environment variables and settings
- [Development](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md) — Architecture, dev setup, and Claude Code workflow

## Development

The development environment runs entirely inside Docker — no Python on the host. See [docs/DEVELOPMENT.md](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md) for the full setup, including how to run tests, linters, and install the pre-commit hook.

## Built with Claude Code

This project is developed with [Claude Code](https://claude.ai/code), Anthropic's AI coding assistant. Custom skills and commands are provided in `.claude/` to maintain project conventions and support a structured dev workflow. See [docs/DEVELOPMENT.md](https://github.com/cibrandocampo/ovh-dyndns-client/blob/main/docs/DEVELOPMENT.md#claude-code) for details.

## Links

- [Project website](https://cibrandocampo.github.io/ovh-dyndns-client/) — Marketing landing with screenshots and self-host walkthrough
- [GitHub Repository](https://github.com/cibrandocampo/ovh-dyndns-client)
- [Docker Hub](https://hub.docker.com/r/cibrandocampo/ovh-dyndns-client)
- [OVH DynHost Documentation](https://docs.ovh.com/gb/en/domains/hosting_dynhost/)

## Support

- **Issues**: [GitHub Issues](https://github.com/cibrandocampo/ovh-dyndns-client/issues)
- **Email**: [hello@cibran.es](mailto:hello@cibran.es)

## License

Released under the [MIT License](LICENSE) © 2022 Cibrán Docampo Piñeiro.

You are free to **use**, **modify**, **distribute**, and **self-host** this software — personally or commercially — as long as the original copyright notice is preserved. No warranty is provided.
