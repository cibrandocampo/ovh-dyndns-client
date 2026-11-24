# REST API Documentation

All API endpoints require JWT authentication except `/api/auth/login`, `/health` and `/api/version`.

## Authentication

### Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "your-password"}'
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIs...",
  "token_type": "bearer",
  "must_change_password": false
}
```

**Note**: when `must_change_password` is `true` in the response, every
endpoint other than `POST /api/auth/change-password` will return
`403 Password change required` until the password is rotated. This
applies to the default `admin/admin` account on first deployment.

### Using the Token

Include the token in the `Authorization` header:

```bash
curl http://localhost:8000/api/hosts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Change Password

```bash
curl -X POST http://localhost:8000/api/auth/change-password \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"current_password": "old-pass", "new_password": "new-pass"}'
```

The new password must be 6 to 72 bytes long. The change revokes every token
issued before it; the response carries a new `access_token` to keep using.

### Rate limiting

Authentication endpoints are rate-limited per client IP:

- `POST /api/auth/login` — 5 requests per minute
- `POST /api/auth/change-password` — 10 requests per minute

Exceeding the limit returns `429 Too Many Requests`. See
[Rate limiting](CONFIGURATION.md#rate-limiting) for the full reference,
including reverse proxy considerations.

## Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Get JWT token |
| POST | `/api/auth/change-password` | Change password |
| GET | `/api/hosts/` | List all hosts |
| POST | `/api/hosts/` | Create a new host |
| GET | `/api/hosts/{id}` | Get host by ID |
| PUT | `/api/hosts/{id}` | Update host |
| DELETE | `/api/hosts/{id}` | Delete host |
| GET | `/api/status/` | Get current IP and host status |
| POST | `/api/status/trigger` | Trigger immediate DNS update |
| GET | `/api/history/` | Get history (paginated) |
| GET | `/api/settings/` | Get settings |
| PUT | `/api/settings/` | Update settings |
| GET | `/health` | Health check (no auth required) |
| GET | `/api/version` | Application version (no auth required) |

## Hosts

### List Hosts

```bash
curl http://localhost:8000/api/hosts/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Create Host

```bash
curl -X POST http://localhost:8000/api/hosts/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "hostname": "example.com",
    "username": "dynhost-user",
    "password": "dynhost-pass"
  }'
```

`hostname` must be a fully qualified domain name (letters, digits, hyphens and
dots); `username` and `password` must not be empty. Invalid input returns
`422`; a hostname that already exists returns `409`.

### Update Host

```bash
curl -X PUT http://localhost:8000/api/hosts/1 \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"hostname": "new-hostname.com"}'
```

Only the fields sent are changed, with the same validation as on create.
Changing the hostname, username or password marks the host as pending, so it
is updated on the next cycle.

### Delete Host

```bash
curl -X DELETE http://localhost:8000/api/hosts/1 \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Status

### Get Current Status

```bash
curl http://localhost:8000/api/status/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "current_ip": "84.236.194.230",
  "last_check": "2026-01-30T16:34:39",
  "hosts": [
    {
      "id": 1,
      "hostname": "example.com",
      "last_update": "2026-01-30T16:34:39",
      "last_status": true,
      "last_error": null
    }
  ]
}
```

### Trigger Manual Update

```bash
curl -X POST http://localhost:8000/api/status/trigger \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## History

### Get History (Paginated)

```bash
curl "http://localhost:8000/api/history/?limit=20&offset=0" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

Response:
```json
{
  "entries": [
    {
      "id": 1,
      "ip": "84.236.194.230",
      "timestamp": "2026-01-30T16:34:39",
      "action": "ip_changed",
      "hostname": null,
      "details": "IP changed from null to 84.236.194.230"
    }
  ],
  "total": 1,
  "limit": 20,
  "offset": 0
}
```

## Settings

### Get Settings

```bash
curl http://localhost:8000/api/settings/ \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Update Settings

```bash
curl -X PUT http://localhost:8000/api/settings/ \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"update_interval": 600}'
```

## Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
