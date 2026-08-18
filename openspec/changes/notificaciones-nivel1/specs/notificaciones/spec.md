# notificaciones Specification

## Purpose

Persistent, multi-tenant notification system for gym staff. Provides idempotent generation from membership expirations and calendar events, unread-only list API, per-item and bulk read actions, and unread count for badge display.

## Requirements

### Requirement: Notification Model

The system SHALL have a `Notification` model with fields: `gimnasio` FK (multi-tenant), `tipo` (choices: `por_vencer`, `vencida`, `evento`), `titulo` CharField, `mensaje` TextField, `fecha` DateField, `relacion_tipo` CharField(50) nullable, `relacion_id` IntegerField nullable, `link` TextField, `whatsapp_link` TextField nullable, `is_read` BooleanField default False, `read_at` DateTimeField nullable, `created_at` auto_now_add. A `UniqueConstraint(gimnasio, relacion_tipo, relacion_id, tipo)` SHALL enforce idempotency.

#### Scenario: Notification creation with unique constraint

- GIVEN a gym with id=1 and an existing notification with relacion_tipo='membership', relacion_id=100, tipo='por_vencer'
- WHEN attempting to create another notification with same gimnasio, relacion_tipo, relacion_id, tipo
- THEN the creation fails with IntegrityError (unique constraint violation)

#### Scenario: Different tipo allows duplicate source

- GIVEN a gym with id=1 and an existing notification with relacion_tipo='membership', relacion_id=100, tipo='por_vencer'
- WHEN creating a notification with same gimnasio, relacion_tipo, relacion_id, but tipo='vencida'
- THEN the creation succeeds (different tipo allowed)

### Requirement: Idempotent Notification Generation

The system SHALL provide `NotificationManager.generate_for_gimnasio(gimnasio)` that uses `get_or_create` to generate notifications without duplication. Generation SHALL be triggered lazily inside the list endpoint (no scheduled jobs). Sources: memberships (expiring within 3 days exclusive of today, expired) and calendar events with `fecha_inicio` on the same day (per gym timezone).

#### Scenario: First list call generates notifications

- GIVEN a gym with memberships expiring in 2 days and an event starting today
- WHEN the list endpoint is called for the first time
- THEN two notifications are created (por_vencer for membership, evento for event)
- AND the list returns these two unread notifications

#### Scenario: Second list call does not duplicate

- GIVEN a gym with already generated notifications for expiring memberships
- WHEN the list endpoint is called again
- THEN no new notifications are created (get_or_create returns existing)
- AND the list returns the same notifications

#### Scenario: Membership expired generates vencida

- GIVEN a gym with a membership whose dateFinal is today or earlier
- WHEN generation runs
- THEN a notification with tipo='vencida' is created

#### Scenario: Membership expiring generates por_vencer

- GIVEN a gym with a membership whose dateFinal is within next 3 days (exclusive of today)
- WHEN generation runs
- THEN a notification with tipo='por_vencer' is created

#### Scenario: Event happening today generates evento

- GIVEN a gym with an EventoCalendario where fecha_inicio falls on today's date (local gym timezone)
- WHEN generation runs
- THEN a notification with tipo='evento' is created

### Requirement: Notification Read State

The system SHALL treat unread as `read_at IS NULL`. Read notifications SHALL disappear from the list (list returns only unread). Per-item read SHALL set `is_read=True` and `read_at=timezone.now()`. Bulk read SHALL mark all unread notifications as read.

#### Scenario: Per-item read

- GIVEN an unread notification with id=1
- WHEN POST to `{id}/marcar-leida/`
- THEN `is_read` becomes True and `read_at` is set
- AND the notification no longer appears in the list

#### Scenario: Bulk read

- GIVEN three unread notifications for a gym
- WHEN POST to `marcar-todas-leidas/`
- THEN all three notifications have `is_read=True` and `read_at` set
- AND the list returns empty

#### Scenario: Unread count

- GIVEN two unread notifications and one read notification for a gym
- WHEN GET to `no-leidas/`
- THEN response is `{"count": 2}`

### Requirement: Multi-Tenant Isolation

The system SHALL filter all notification queries by `gimnasio=request.gimnasio`. Notifications from gym A SHALL NOT be visible to gym B.

#### Scenario: Cross-gym isolation

- GIVEN gym A with notifications and gym B with notifications
- WHEN a staff user from gym A calls the list endpoint
- THEN only gym A's unread notifications are returned

### Requirement: Permission Enforcement

The system SHALL allow access only to users with roles 'admin' or 'recepcion' (IsRecepcionUser). Recepcion users SHALL NOT be able to delete notifications (if delete action exists).

#### Scenario: Admin access

- GIVEN a user with role 'admin'
- WHEN calling any notification endpoint
- THEN access is granted

#### Scenario: Recepcion access

- GIVEN a user with role 'recepcion'
- WHEN calling list, read, or count endpoints
- THEN access is granted

#### Scenario: Unauthorized access

- GIVEN an unauthenticated user
- WHEN calling any notification endpoint
- THEN 401 Unauthorized is returned

### Requirement: API Endpoints

The system SHALL provide: GET `/Notificaciones/` (unread only, ordered `-created_at`), POST `/Notificaciones/{id}/marcar-leida/`, POST `/Notificaciones/marcar-todas-leidas/`, GET `/Notificaciones/no-leidas/`. Legacy endpoints `membership-notifications` and `mark-notifications-read` SHALL be removed.

#### Scenario: List returns unread only

- GIVEN three unread and two read notifications
- WHEN GET `/Notificaciones/`
- THEN response contains three notifications (unread only)

#### Scenario: Legacy endpoint removed

- GIVEN the legacy endpoint `/membership-notifications/`
- WHEN calling GET `/membership-notifications/`
- THEN 404 Not Found is returned

### Requirement: Notification Content

The system SHALL generate `titulo` and `mensaje` in Spanish (matching current behavior). `whatsapp_link` SHALL be generated using the member's phone with hardcoded country code 57. `link` for membership notifications SHALL point to `/dashboard/asignar-membresia-list` (not the deleted detail route).

#### Scenario: Membership notification link

- GIVEN a membership notification for membership id=123
- WHEN the notification is created
- THEN `link` is `/dashboard/asignar-membresia-list`
- AND `whatsapp_link` includes the member's phone with prefix 57

#### Scenario: Event notification link

- GIVEN an event notification for event id=456
- WHEN the notification is created
- THEN `link` includes `?evento=456` for calendar deep link

### Requirement: Known Limitations (Nivel 1)

Stale reminders on moved events are accepted (unique key prevents regeneration). Previously-dismissed expirations may reappear unread once after deploy (backfill semantics). The `notified_at` column is kept but deprecated (help_text).

#### Scenario: Event move stale reminder

- GIVEN an event notification generated for event id=100 at time T
- WHEN the event's fecha_inicio is moved to a different day
- THEN the old notification remains (unique key prevents new generation)
- AND the stale reminder is accepted for Nivel 1

#### Scenario: Post-deploy reappearance

- GIVEN memberships that were previously dismissed via notified_at
- WHEN the system deploys the new Notification model
- THEN those memberships may generate new unread notifications once
- AND this is expected one-time behavior