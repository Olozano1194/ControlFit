# EventoCalendario Specification

## Purpose

Multi-tenant CRUD for calendar events. Each event belongs to a gym and optionally references a TipoEvento. Supports range filtering via `?start=&end=` overlap semantics, nested `tipo_detalle` representation, and automatic `created_by` assignment.

## Requirements

### Requirement: EventoCalendario CRUD with IsRecepcionUser permission

The system MUST expose a full CRUD API for EventoCalendario scoped to the authenticated user's gym. Users with role `admin` or `recepcion` MAY create, read, update, and delete events. Unauthenticated users MUST NOT access this endpoint.

#### Scenario: Authenticated user creates an EventoCalendario

- GIVEN an authenticated recepcion user belonging to gym G1
- WHEN the user POSTs `{ "titulo": "Yoga", "fecha_inicio": "2026-08-15T10:00:00Z", "fecha_fin": "2026-08-15T12:00:00Z" }` to `/gym/api/v1/CalendarioEventos/`
- THEN the system creates the event with `gimnasio = G1`, `created_by = request.user.id`, returns 201

#### Scenario: Unauthenticated access is rejected

- GIVEN no authentication token
- WHEN a user attempts to GET `/gym/api/v1/CalendarioEventos/`
- THEN the system returns 401 Unauthorized

### Requirement: EventoCalendario includes nested tipo_detalle

The system MUST include a `tipo_detalle` field in the serialized response. When `tipo` is provided, `tipo_detalle` MUST contain `{ id, nombre, color }` from the referenced TipoEvento. When `tipo` is null, `tipo_detalle` MUST be null.

#### Scenario: Event with linked TipoEvento

- GIVEN EventoCalendario E1 has `tipo = T1` (nombre="Clase", color="#FF0000")
- WHEN the system serializes E1
- THEN the response includes `"tipo_detalle": { "id": T1.id, "nombre": "Clase", "color": "#FF0000" }`

#### Scenario: Event without TipoEvento

- GIVEN EventoCalendario E2 has `tipo = null`
- WHEN the system serializes E2
- THEN the response includes `"tipo_detalle": null`

### Requirement: Range filter with overlap semantics

The system MUST support `?start=<datetime>&end=<datetime>` query parameters on list. When provided, the system MUST return only events where `fecha_inicio <= end AND fecha_fin >= start` (overlap semantics). Events MUST be ordered by `fecha_inicio` ascending.

#### Scenario: Filter returns overlapping events

- GIVEN events E1 (start=2026-08-15T08:00, end=2026-08-15T10:00) and E2 (start=2026-08-15T09:00, end=2026-08-15T11:00)
- WHEN the user GETs `?start=2026-08-15T09:30:00Z&end=2026-08-15T10:30:00Z`
- THEN both E1 and E2 are returned (both overlap the query window)

#### Scenario: Filter excludes non-overlapping events

- GIVEN event E3 (start=2026-08-15T08:00, end=2026-08-15T09:00)
- WHEN the user GETs `?start=2026-08-15T10:00:00Z&end=2026-08-15T12:00:00Z`
- THEN E3 is NOT returned (ends before the query window)

#### Scenario: No filter returns all gym events

- GIVEN gym G1 has 5 EventoCalendario records
- WHEN the user GETs `/gym/api/v1/CalendarioEventos/` without query params
- THEN all 5 events are returned, ordered by `fecha_inicio` ascending

### Requirement: EventoCalendario isolation across gyms

The system MUST ensure that EventoCalendario records are strictly scoped to their owning gym. No user may read or modify records belonging to a different gym.

#### Scenario: List scoped to caller's gym

- GIVEN gym G1 has 3 events and gym G2 has 2 events
- WHEN a user from G1 GETs `/gym/api/v1/CalendarioEventos/`
- THEN only G1's 3 events are returned

### Requirement: Nullable fields are accepted

The system MUST accept null values for `tipo`, `relacion_tipo`, `relacion_id`, `created_by`, and `descripcion`. No polymorphic logic applies to `relacion_tipo`/`relacion_id`; they are stored as plain optional fields.

#### Scenario: Create with all optional fields null

- GIVEN an authenticated user from gym G1
- WHEN the user POSTs `{ "titulo": "Reunión", "fecha_inicio": "...", "fecha_fin": "...", "tipo": null, "relacion_tipo": null, "relacion_id": null }`
- THEN the system creates the event with those fields as null

### Requirement: fecha_inicio and fecha_fin are DateTimeFields

The system MUST accept ISO 8601 datetime strings for `fecha_inicio` and `fecha_fin`. Both fields are required on create. The `fecha_fin` MUST be after `fecha_inicio`.

#### Scenario: Invalid datetime format returns 400

- GIVEN an authenticated user
- WHEN the user POSTs with `fecha_inicio = "not-a-date"`
- THEN the system returns 400 Bad Request with datetime validation error

#### Scenario: fecha_fin before fecha_inicio returns 400

- GIVEN an authenticated user
- WHEN the user POSTs `fecha_fin` before `fecha_inicio`
- THEN the system returns 400 Bad Request
