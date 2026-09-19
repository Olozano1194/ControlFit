# TipoEvento Specification

## Purpose

Multi-tenant CRUD for calendar event types. Each gym owns its own set of event types (nombre, color). Only admin users may manage them; other authenticated users read them for calendar rendering.

## Requirements

### Requirement: TipoEvento CRUD is admin-only

The system MUST expose a full CRUD API for TipoEvento scoped to the authenticated user's gym. Only users with role `admin` MAY create, update, or delete TipoEvento records. All authenticated users MAY list TipoEvento records for their gym.

#### Scenario: Admin creates a TipoEvento

- GIVEN an authenticated admin user belonging to gym G1
- WHEN the user POSTs `{ "nombre": "Clase", "color": "#FF0000" }` to `/gym/api/v1/TiposEvento/`
- THEN the system creates a TipoEvento with `gimnasio = G1`, returns 201 with `{ id, nombre, color, gimnasio, created_at }`

#### Scenario: Recepcion user cannot create TipoEvento

- GIVEN an authenticated recepcion user belonging to gym G1
- WHEN the user POSTs a TipoEvento to `/gym/api/v1/TiposEvento/`
- THEN the system returns 403 Forbidden

#### Scenario: List returns only caller's gym types

- GIVEN gym G1 has 3 TipoEvento records and gym G2 has 2
- WHEN an authenticated user from G1 GETs `/gym/api/v1/TiposEvento/`
- THEN the system returns exactly the 3 TipoEvento records belonging to G1

### Requirement: TipoEvento isolation across gyms

The system MUST ensure that TipoEvento records are strictly scoped to their owning gym. No user may read or modify TipoEvento records belonging to a different gym.

#### Scenario: Update is scoped to own gym

- GIVEN TipoEvento T1 belongs to gym G1
- WHEN an admin from gym G2 attempts to PUT T1's URL
- THEN the system returns 404 Not Found

#### Scenario: Delete is scoped to own gym

- GIVEN TipoEvento T1 belongs to gym G1
- WHEN an admin from gym G1 deletes T1
- THEN T1 is removed and subsequent GETs no longer include it

### Requirement: TipoEvento required fields

The system MUST validate that `nombre` and `color` are provided on create. The `created_at` field MUST be set automatically. The `gimnasio` field MUST be set automatically from the request context.

#### Scenario: Missing required fields returns 400

- GIVEN an authenticated admin user
- WHEN the user POSTs `{ "nombre": "Clase" }` without `color`
- THEN the system returns 400 Bad Request with validation error

#### Scenario: Null tipo is valid on EventoCalendario

- GIVEN an EventoCalendario record
- WHEN the `tipo` field is null
- THEN the system accepts the record (tipo is nullable)
