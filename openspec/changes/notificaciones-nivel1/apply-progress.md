# Apply Progress: notificaciones-nivel1 — Slice 1 (Backend)

**Change**: notificaciones-nivel1
**Slice**: 1 — Backend (phases 1-3, tasks 1.1-3.8)
**Mode**: Strict TDD (test runner: `env\Scripts\python.exe manage.py test`)
**Delivery**: Chained PRs (stacked-to-main) — PR 1 backend (this slice), PR 2 frontend (later run)
**Branch**: `OscarL` (no PRs created — user merges manually on GitHub)
**Date**: 2026-08-18

## Summary

Backend notification foundation implemented and verified: persistent multi-tenant `Notification` model with idempotency UniqueConstraint, lazy idempotent generation service (`NotificationManager.generate_for_gimnasio`), `NotificationSerializer`, `NotificationViewSet` (list unread-only + marcar-leida + marcar-todas-leidas + no-leidas), router registration, and full removal of the two legacy function-based endpoints. 24 new tests written (model 3, manager 10, ViewSet 11); full suite green: **103/103** (79 existing + 24 new). `manage.py check` passes.

## Completed Tasks (1.1 - 3.8)

All 17 backend tasks complete and marked `[x]` in `tasks.md`:

- [x] 1.1 Notification model (gimnasio FK, tipo choices, titulo/mensaje/fecha, polymorphic relacion_tipo/id, link, whatsapp_link, is_read, read_at, created_at, UniqueConstraint uq_notification_idempotency, db_table='notification', ordering -created_at)
- [x] 1.2 Migration 0008_alter_membresiaasignada_notified_at_notification (non-destructive: new table + notified_at help_text deprecation)
- [x] 1.3 migrate + manage.py check
- [x] 2.1 gimnasioApp/services/__init__.py
- [x] 2.2 gimnasioApp/services/notifications.py — NotificationManager.generate_for_gimnasio: por_vencer (hoy, hoy+3], vencida (<= hoy), evento (fecha_inicio__date=today); Spanish titulo/mensaje; whatsapp_link prefijo 57; link memberships → /dashboard/asignar-membresia-list, eventos → /dashboard/calendar?evento=<id>
- [x] 2.3 NotificationSerializer (read_only: id, gimnasio, is_read, read_at, created_at)
- [x] 2.4 NotificationViewSet — MultiTenantViewSetMixin + ReadOnlyModelViewSet, [IsAuthenticated, IsRecepcionUser]; list (genera + solo no leídas, -created_at), marcar_leida, marcar_todas_leidas, no_leidas
- [x] 2.5 urls.py — router.register Notificaciones; legacy paths removed
- [x] 2.6 Legacy views membership_notifications + mark_notifications_read deleted; unused imports (api_view, permission_classes) removed
- [x] 3.1 Idempotency test
- [x] 3.2 Multi-tenant isolation test
- [x] 3.3 Permission enforcement tests (401 / 403)
- [x] 3.4 Read state tests (single + bulk + count)
- [x] 3.5 Generation trigger tests (list endpoint)
- [x] 3.6 Edge case tests (empty gym, sin phone, frontera media noche, evento mañana, ya leídas excluidas)
- [x] 3.7 Legacy endpoint removal test (404)
- [x] 3.8 Full suite green

## TDD Cycle Evidence

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1-1.3 (model) | `gimnasioApp/tests.py` — NotificationModelTest | Unit (django TestCase) | ✅ 79/79 | ✅ Written (ImportError Notification) | ✅ 3/3 passed | ✅ 3 cases (duplicate/different tipo/defaults) | ✅ Clean |
| 2.1-2.2 (services) | `gimnasioApp/tests.py` — NotificationManagerTest | Unit (django TestCase) | ✅ 79/79 | ✅ Written (ImportError NotificationManager) | ✅ 10/10 passed | ✅ 10 cases (expiring/expired/event/idempotency/phone/fronteras) | ✅ Clean |
| 2.3-2.6 (API+legacy) | `gimnasioApp/tests.py` — NotificationViewSetTest | Integration (APIRequestFactory + force_authenticate) | ✅ 79/79 | ✅ Written (ImportError NotificationViewSet) | ✅ 11/11 passed (1 fix en helper de datos, no en producción) | ✅ 11 cases (permisos/aislamiento/lectura/legacy) | ✅ Clean (get_queryset reutilizado en acciones) |
| 3.8 (full suite) | `gimnasioApp/tests.py` | Unit+Integration | — | — | ✅ 103/103 passed | — | — |

## Work Unit Evidence

| Evidence | Value |
|---|---|
| Focused test command and exact result | Commit 1: `env\Scripts\python.exe manage.py test gimnasioApp.tests.NotificationModelTest` → OK 3/3. Commit 2: `.test.NotificationManagerTest` → OK 10/10; `.test.NotificationViewSetTest` → OK 11/11. Final: `manage.py test gimnasioApp` → Ran 103 tests, OK |
| Runtime harness command/scenario and exact result | N/A — backend unit/integration tests only; no runtime boundary beyond the Django test runner (no Celery, no external services; DRF endpoints exercised via APIRequestFactory). `manage.py check` → "System check identified no issues" |
| Rollback boundary | `git revert` of commits `8c4ac73` + `5de8321` removes: Notification model, migration 0008, services/, NotificationSerializer, NotificationViewSet, urls entry, and restores legacy endpoints/views. Frontend untouched. No destructive migration (table `notification` is additive; `notified_at` column kept). |

## Files Changed

| File | Action | What Was Done |
|------|--------|---------------|
| `gimnasioApp/models.py` | Modified | +`Notification` model (+56 lines); deprecate `notified_at` help_text on MembresiaAsignada |
| `gimnasioApp/migrations/0008_alter_membresiaasignada_notified_at_notification.py` | Created | Non-destructive: new `notification` table + help_text alter |
| `gimnasioApp/services/__init__.py` | Created | Package init |
| `gimnasioApp/services/notifications.py` | Created | `NotificationManager` — generate_for_gimnasio (get_or_create idempotente, 3 fuentes), helpers privados, prefijo 57 |
| `gimnasioApp/serializers.py` | Modified | +`NotificationSerializer` |
| `gimnasioApp/views.py` | Modified | +`NotificationViewSet` (4 acciones); deleted `membership_notifications` + `mark_notifications_read`; import cleanup (api_view/permission_classes removed, action added) |
| `gimnasioApp/urls.py` | Modified | +router.register Notificaciones; legacy path entries removed |
| `gimnasioApp/tests.py` | Modified | +24 tests (NotificationModelTest 3, NotificationManagerTest 10, NotificationViewSetTest 11) |

## Test Summary

- **Total tests written**: 24
- **Total tests passing**: 103 (79 existing + 24 new) — full suite OK
- **Layers used**: Unit (13), Integration (11)
- **Approval tests** (refactoring): 2 — legacy endpoints 404 (removal captured by test)
- **Pure functions created**: 1 (`_construir_whatsapp_link`)

## Deviations from Design

None — implementation matches design.md exactly. Notes for clarity:
- `NotificationManager` is implemented as a plain class with classmethods in `services/notifications.py` (not a Django model Manager), matching the spec call signature `NotificationManager.generate_for_gimnasio(gimnasio)` and avoiding a circular import models ↔ services.
- `NotificationViewSet` uses `ReadOnlyModelViewSet` (no create/update/delete exposed at all — stricter than the spec's "recepcion cannot delete"; no client needs write access since generation is automatic).
- Event notification title is "Evento programado hoy" (design specified Spanish content but not the exact event string).

## Issues Found

1. **Test data collision (resolved)**: the ViewSet test helper initially used low `relacion_id` values that collided with real `EventoCalendario` ids in the test DB, so `get_or_create` returned a pre-existing *read* notification. Fixed by using a high id space (100000+) in the helper. Production code was correct.
2. **WARNING — frontend temporarily broken by design**: `gimnasioReact/src/api/action/notifications.api.ts` still calls the removed legacy endpoints (`/membership-notifications/`, `/membership-notifications/read/`). Until Slice 2 (PR 2) lands, the notification menu/page will hit 404. Expected consequence of the stacked-to-main chained split; Slice 2 is the immediate next run.
3. **INFO — test DB is MySQL**: `MySQLdb.IntegrityError` confirms the constraint works on the real DB engine; the timezone rule `date.today()` (UTC) was verified empirically (`timezone.now()` 2026-08-18T08:05Z matched local date).

## Remaining Tasks (Slice 2 — Frontend, NOT in this run)

- [ ] 4.1 Replace notifications.model.ts (new interface)
- [ ] 4.2 Replace notifications.api.ts (4 functions: getNotifications, getUnreadCount, markOneRead, markAllAsRead)
- [ ] 5.1 NotificationMenu.tsx — real badge, per-item read, stable keys, new icon mapping, 5-min poll, empty state
- [ ] 5.2 NotificationsPage.tsx — list, per-item read, markAllAsRead, link field, loading/error
- [ ] 5.3 CalendarioPage.tsx — ?evento=<id> deep link
- [ ] 6.1-6.7 Frontend verification (tsc -b, build, manual QA)

## Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main), PR 1 of 2
- Work unit: Backend notification foundation (tasks 1.1-3.8)
- Boundary: starts at `c12a413` (pre-slice state), ends at commit `5de8321`; frontend files untouched
- Estimated review budget: ~660 changed lines backend (commit 1: 235+, commit 2: 424+/133-) — above the 400-line budget, which is why the change is chained; this is the accepted delivery decision (slice 1 backend, slice 2 frontend)

## Commits Made

1. `8c4ac73` feat(notificaciones): modelo Notification persistente y generador idempotente — models.py, migration 0008, services/
2. `5de8321` feat(notificaciones): API de notificaciones y eliminacion de endpoints legacy — serializers.py, views.py, urls.py, tests.py

(No AI attribution, conventional commits en español, repo convention.)