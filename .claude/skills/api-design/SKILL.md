---
name: api-design
description: REST API design conventions — URL structure, HTTP semantics, response format, error handling, and versioning. Use when designing or reviewing API endpoints.
---

# API Design

## URL Structure

- **Lowercase, hyphen-separated**: `/api/user-profiles/`, not `/api/userProfiles/`
- **Nouns, not verbs**: `/api/orders/`, not `/api/getOrders/`
- **Plural resources**: `/api/orders/`, `/api/orders/{id}/`
- **Nested resources** only when the relationship is strong and the child never exists without the parent: `/api/orders/{id}/items/`
- **Trailing slash**: be consistent — pick one convention and enforce it everywhere
- **Versioning**: prefix with `/api/v1/` if breaking changes are anticipated

## HTTP Methods

| Method | Use | Body | Idempotent |
|--------|-----|------|-----------|
| `GET` | Read — list or detail | None | Yes |
| `POST` | Create | Required | No |
| `PUT` | Full replace | Required | Yes |
| `PATCH` | Partial update | Required | Yes |
| `DELETE` | Remove | None | Yes |

Never use `GET` for operations with side effects. Never use `POST` for reads.

## Status Codes

| Code | When to use |
|------|-------------|
| `200 OK` | Successful GET, PATCH, PUT |
| `201 Created` | Successful POST that creates a resource |
| `204 No Content` | Successful DELETE or action with no response body |
| `400 Bad Request` | Validation error — the client sent invalid data |
| `401 Unauthorized` | Not authenticated |
| `403 Forbidden` | Authenticated but not authorised |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | State conflict (e.g. duplicate, version mismatch) |
| `422 Unprocessable Entity` | Semantically invalid request (use sparingly; prefer 400) |
| `500 Internal Server Error` | Unexpected server failure |

Never return `200` with an error body. Never return `500` for client mistakes.

## Response Format

### Success — list

```json
{
  "results": [...],
  "count": 42,
  "next": "https://api.example.com/api/v1/orders/?page=3",
  "previous": "https://api.example.com/api/v1/orders/?page=1"
}
```

### Success — single resource

```json
{
  "id": "uuid-or-int",
  "field": "value",
  "created_at": "2025-01-15T10:30:00Z"
}
```

### Error

```json
{
  "error": "Human-readable message for the developer",
  "code": "SNAKE_CASE_ERROR_CODE",
  "details": {
    "field_name": ["Specific validation message"]
  }
}
```

- `error`: always present, human-readable
- `code`: always present, machine-readable constant (use in client error handling)
- `details`: optional, for field-level validation errors

## Conventions

### Dates and times
- Always ISO 8601 UTC: `"2025-01-15T10:30:00Z"`
- Never timestamps, locale-formatted strings, or ambiguous formats

### IDs
- Expose UUIDs or opaque strings to clients — never auto-increment integers that reveal record counts
- Exception: internal/admin APIs where leaking record counts is acceptable

### Booleans and nulls
- Use explicit `true`/`false`, never `1`/`0` or `"yes"`/`"no"`
- Avoid returning `null` for missing optional fields — omit the key or return an empty value appropriate to the type

### Pagination
- Always paginate list endpoints — never return unbounded lists
- Default page size: document it; enforce a maximum

### Filtering and sorting
- Filters as query params: `?status=active&created_after=2025-01-01`
- Sorting: `?ordering=created_at` or `?ordering=-created_at` (prefix `-` for descending)

## What NOT to Do

- Don't put actions in URLs: `/api/orders/123/cancel/` is acceptable as a special action, but prefer `PATCH /api/orders/123/` with `{"status": "cancelled"}` when the state change is simple
- Don't leak internal implementation details (table names, ORM errors, stack traces) in responses
- Don't design endpoints around your ORM models — design around what the client needs
- Don't invent new conventions when an established one exists
