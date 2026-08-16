# CalendarioPublico Specification

## Purpose

Unauthenticated public endpoint to read all calendar events for a specific gym, ordered by start date. Used by external consumers or public-facing pages that do not require login.

## Requirements

### Requirement: Public endpoint returns all events for a gym

The system MUST expose `GET /api/calendario/publico/{gimnasio_id}/` with `AllowAny` permission (no authentication required). The endpoint MUST return all EventoCalendario records belonging to the specified gym, ordered by `fecha_inicio` ascending.

#### Scenario: Valid gimnasio_id returns events

- GIVEN gym G1 exists with 3 EventoCalendario records
- WHEN a request is made to `/api/calendario/publico/{G1.id}/`
- THEN the system returns all 3 events, ordered by `fecha_inicio` ascending
- AND the response includes `tipo_detalle` nested representation

#### Scenario: Public endpoint is not under /gym/api/v1

- GIVEN the public endpoint is at `/api/calendario/publico/{id}/`
- WHEN a consumer calls the endpoint
- THEN the URL does NOT start with `/gym/api/v1/`

### Requirement: Public endpoint returns 404 for nonexistent gym

The system MUST return 404 Not Found when the `gimnasio_id` in the URL does not match any active Gimnasio record.

#### Scenario: Unknown gimnasio_id

- GIVEN no gym with id=99999 exists
- WHEN a request is made to `/api/calendario/publico/99999/`
- THEN the system returns 404 Not Found

### Requirement: Public endpoint is read-only

The system MUST ONLY support GET method on the public endpoint. POST, PUT, PATCH, DELETE MUST return 405 Method Not Allowed.

#### Scenario: POST to public endpoint

- WHEN a request POSTs to `/api/calendario/publico/1/`
- THEN the system returns 405 Method Not Allowed

### Requirement: Public endpoint returns empty list for gym with no events

The system MUST return an empty array `[]` when the specified gym exists but has no EventoCalendario records.

#### Scenario: Gym exists with no events

- GIVEN gym G2 exists with 0 EventoCalendario records
- WHEN a request is made to `/api/calendario/publico/{G2.id}/`
- THEN the system returns 200 OK with `[]`
