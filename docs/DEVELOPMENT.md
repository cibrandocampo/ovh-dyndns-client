# Development Guide

## Development Environment

This project includes a Docker-based development environment.

### Quick Start

```bash
cd dev/
make build
make up
make shell
```

### Available Commands

| Command | Description |
|---------|-------------|
| `make build` | Build the development Docker image |
| `make up` | Start the development container |
| `make down` | Stop the development container |
| `make shell` | Open a shell in the container |
| `make test` | Run tests |
| `make test-cov` | Run tests with coverage |
| `make lint` | Run linting checks |
| `make format` | Format code with black |
| `make logs` | Show container logs |
| `make clean` | Clean up containers and images |

## Project Structure

```
src/
├── api/                          # REST API layer
│   ├── main.py                   # FastAPI application
│   ├── auth.py                   # JWT authentication
│   ├── dependencies.py           # API dependencies
│   └── routers/                  # API endpoints
│       ├── auth.py               # Authentication endpoints
│       ├── hosts.py              # Hosts CRUD
│       ├── status.py             # Status and trigger
│       ├── history.py            # History endpoint
│       └── settings.py           # Settings management
├── application/                  # Application layer
│   ├── controller.py             # Main orchestrator
│   └── ports/                    # Port interfaces
│       ├── dns_updater.py        # DNS update port
│       ├── hosts_repository.py   # Hosts repository port
│       ├── ip_provider.py        # IP provider port
│       └── ip_state_store.py     # IP state storage port
├── domain/                       # Domain layer
│   └── hostconfig.py             # Host configuration model
├── infrastructure/               # Infrastructure layer
│   ├── clients/                  # External service adapters
│   │   ├── ipify_client.py       # Implements IpProvider
│   │   └── ovh_client.py         # Implements DnsUpdater
│   ├── database/                 # Database layer
│   │   ├── models.py             # SQLAlchemy models
│   │   ├── database.py           # Database connection
│   │   └── repository.py         # Implements IpStateStore & HostsRepository
│   ├── config.py                 # Environment configuration
│   └── logger.py                 # Logging system
├── static/                       # Frontend assets
│   ├── index.html                # Main HTML page
│   ├── css/style.css             # Styles
│   └── js/app.js                 # Frontend JavaScript
├── test/                         # Unit tests
└── main.py                       # Entry point
```

## Architecture

The application uses **hexagonal architecture** (ports and adapters):

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (HTML/JS)                       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI REST API                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 Application Layer                           │
│              (Controller + Ports)                           │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│   SQLite        │ │   Ipify         │ │   OVH API       │
│   Repository    │ │   Client        │ │   Client        │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Key Concepts

- **Ports**: Abstract interfaces (`IpProvider`, `DnsUpdater`, `IpStateStore`, `HostsRepository`)
- **Adapters**: Concrete implementations (`IpifyClient`, `OvhClient`, `SqliteRepository`)
- **Dependency Injection**: `main.py` wires dependencies together

### Benefits

- **Testability**: Easy to mock dependencies
- **Flexibility**: Swap implementations without changing business logic
- **Separation of concerns**: Clear boundaries between layers

## Database Schema

```sql
-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    must_change_password BOOLEAN DEFAULT TRUE
);

-- Hosts table
CREATE TABLE hosts (
    id INTEGER PRIMARY KEY,
    hostname TEXT UNIQUE NOT NULL,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    last_update DATETIME,
    last_status BOOLEAN,
    last_error TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- State table
CREATE TABLE state (
    id INTEGER PRIMARY KEY DEFAULT 1,
    current_ip TEXT,
    last_check DATETIME
);

-- History table
CREATE TABLE history (
    id INTEGER PRIMARY KEY,
    ip TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    action TEXT,
    hostname TEXT,
    details TEXT
);

-- Settings table
CREATE TABLE settings (
    id INTEGER PRIMARY KEY DEFAULT 1,
    update_interval INTEGER DEFAULT 300,
    logger_level TEXT DEFAULT 'INFO'
);
```

## Running Tests

```bash
# Using development environment
cd dev/
make test

# With coverage
make test-cov

# Or run directly
python -m pytest src/test/ -v
```

## Adding New Features

1. **New API endpoint**: Add router in `src/api/routers/`, register in `src/api/routers/__init__.py` and `src/api/main.py`
2. **New database model**: Add to `src/infrastructure/database/models.py`
3. **New port**: Create interface in `src/application/ports/`
4. **New adapter**: Implement in `src/infrastructure/`

## Code Style

- Format with `black`
- Lint with `flake8`
- Type hints encouraged
