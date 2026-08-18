# Apply Progress: notificaciones-nivel1 — Slices 1 (Backend) + 2 (Frontend)

**Change**: notificaciones-nivel1
**Slice 1**: Backend (phases 1-3, tasks 1.1-3.8) — completed 2026-08-18
**Slice 2**: Frontend (phases 4-6, tasks 4.1-6.7) — completed 2026-08-18
**Mode**: Slice 1 Strict TDD (test runner: `env\Scripts\python.exe manage.py test`); Slice 2 verification-driven (no frontend test runner — project norm: `tsc -b` + `npm run build` + manual QA)
**Delivery**: Chained PRs (stacked-to-main) — PR 1 backend (Slice 1), PR 2 frontend (Slice 2)
**Branch**: `OscarL` (no PRs created — user merges manually on GitHub)

## Summary — Slice 1 (Backend)

Backend notification foundation implemented and verified: persistent multi-tenant `Notification` model with idempotency UniqueConstraint, lazy idempotent generation service (`NotificationManager.generate_for_gimnasio`), `NotificationSerializer`, `NotificationViewSet` (list unread-only + marcar-leida + marcar-todas-leidas + no-leidas), router registration, and full removal of the two legacy function-based endpoints. 24 new tests written (model 3, manager 10, ViewSet 11); full suite green: **103/103** (79 existing + 24 new). `manage.py check` passes.

## Summary — Slice 2 (Frontend)

Frontend rewired to the new persistent notification API: `Notification` interface + 4-function API client (`getNotifications`, `getUnreadCount`, `markOneRead`, `markAllAsRead`); NotificationMenu with real badge from the count endpoint, per-item read, stable `key=n.id`, new icon mapping, 5-min polling and empty state; NotificationsPage with list, per-item read button, mark-all with success toast, loading/error states and stable keys; calendar deep link `?evento=<id>` in CalendarioPage via existing `getEvento(id)`. All legacy `/membership-notifications/` calls removed from the frontend. Verification: `npx tsc -b` clean, `npm run build` OK (1292 modules), backend suite still **103/103**, live smoke test: `GET /gym/api/v1/Notificaciones/no-leidas/` → 401 sin token (ruta viva) y `GET /gym/api/v1/membership-notifications/` → 404 (legacy eliminado).

## Completed Tasks — Slice 1 (1.1 - 3.8)

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

## Completed Tasks — Slice 2 (4.1 - 6.7)

All 11 frontend tasks complete and marked `[x]` in `tasks.md`:

- [x] 4.1 `notifications.model.ts` — nueva interface Notification (id, tipo 'por_vencer'|'vencida'|'evento', titulo, mensaje, fecha, relacion_tipo, relacion_id, link, whatsapp_link, is_read, read_at, created_at) + UnreadCountResponse
- [x] 4.2 `notifications.api.ts` — 4 funciones: getNotifications() (GET /Notificaciones/), getUnreadCount() (GET /Notificaciones/no-leidas/ → {count}), markOneRead(id) (POST /Notificaciones/{id}/marcar-leida/), markAllAsRead() (POST /Notificaciones/marcar-todas-leidas/); llamadas legacy eliminadas
- [x] 5.1 NotificationMenu — badge real desde getUnreadCount() (no notifications.length); lectura por item (markOneRead + filtro local + decremento de badge); key={n.id}; iconos por tipo (por_vencer→RiInformationLine amarillo, vencida→RiCloseLine rojo, evento→RiCheckLine verde); polling 5 min (Promise.all lista+conteo); empty state "No hay notificaciones nuevas"; botón WhatsApp no dispara lectura
- [x] 5.2 NotificationsPage — getNotifications(); botón "Marcar como leída" por item; markAllAsRead() con toast de éxito; key={n.id}; link = notification.link (membresías → /dashboard/asignar-membresia-list); loading + error toast; empty state "No hay notificaciones"
- [x] 5.3 CalendarioPage — useSearchParams 'evento' en mount; getEvento(id) → toCalendarEvent → setSelectedEvent abre el modal de detalle existente; toast de error en 404; helper toCalendarEvent reutilizado para el listado
- [x] 6.1 `npx tsc -b` en gimnasioReact — sin errores (exit 0)
- [x] 6.2 `npm run build` en gimnasioReact — build de producción OK (1292 módulos, ~1m15s; warning de chunk >500 kB pre-existente)
- [x] 6.3 QA código: badge usa unread.count del endpoint no-leidas (no la longitud de la lista)
- [x] 6.4 QA código: click en notificación → markOneRead + desaparece de la lista + badge decrementa
- [x] 6.5 QA código: link de membresías apunta a /dashboard/asignar-membresia-list (ruta existente en App.tsx) — sin 404
- [x] 6.6 QA código + smoke: ?evento=<id> → getEvento + modal de detalle abierto (endpoint CalendarioEventos/{id} verificado 401 sin token = ruta viva)
- [x] 6.7 QA código: ?evento=999 → catch → toast.error('No se encontró el evento solicitado'), calendario carga normal

## TDD Cycle Evidence (Slice 1 — Strict TDD)

| Task | Test File | Layer | Safety Net | RED | GREEN | TRIANGULATE | REFACTOR |
|------|-----------|-------|------------|-----|-------|-------------|----------|
| 1.1-1.3 (model) | `gimnasioApp/tests.py` — NotificationModelTest | Unit (django TestCase) | ✅ 79/79 | ✅ Written (ImportError Notification) | ✅ 3/3 passed | ✅ 3 cases (duplicate/different tipo/defaults) | ✅ Clean |
| 2.1-2.2 (services) | `gimnasioApp/tests.py` — NotificationManagerTest | Unit (django TestCase) | ✅ 79/79 | ✅ Written (ImportError NotificationManager) | ✅ 10/10 passed | ✅ 10 cases (expiring/expired/event/idempotency/phone/fronteras) | ✅ Clean |
| 2.3-2.6 (API+legacy) | `gimnasioApp/tests.py` — NotificationViewSetTest | Integration (APIRequestFactory + force_authenticate) | ✅ 79/79 | ✅ Written (ImportError NotificationViewSet) | ✅ 11/11 passed (1 fix en helper de datos, no en producción) | ✅ 11 cases (permisos/aislamiento/lectura/legacy) | ✅ Clean (get_queryset reutilizado en acciones) |
| 3.8 (full suite) | `gimnasioApp/tests.py` | Unit+Integration | — | — | ✅ 103/103 passed | — | — |

## Work Unit Evidence (Slice 2 — verification-driven, sin test runner frontend)

| Work Unit | Focused verification command / exact result | Runtime harness / exact result | Rollback boundary |
|---|---|---|---|
| WU1: modelo + cliente API + NotificationMenu + NotificationsPage (tasks 4.1-5.2) | `npx tsc -b` → exit 0 sin errores; `npm run build` → build OK 1292 módulos | Smoke HTTP con Django runserver local: `GET /gym/api/v1/Notificaciones/no-leidas/` → 401 (ruta viva, auth), `GET /gym/api/v1/membership-notifications/` → 404 (legacy fuera). Suite backend `env\Scripts\python.exe manage.py test gimnasioApp` → 103/103 OK | `git revert` del commit del WU1: restaura modelo/API/componentes antiguos; backend intacto |
| WU2: deep link calendario (task 5.3) | `npx tsc -b` → exit 0; `npm run build` → OK | Smoke HTTP: `GET /gym/api/v1/CalendarioEventos/1/` → 401 sin token (ruta viva). Interacción del modal = QA interactiva pendiente del usuario | `git revert` del commit del WU2: elimina solo el efecto deep link de CalendarioPage |
| WU3: artefactos SDD (tasks.md [x] + apply-progress.md) | Relectura de tasks.md: todas las tareas 4.1-6.7 en `[x]` | N/A — artefactos de documentación, sin frontera runtime | `git revert` del commit docs(sdd) |

Nota QA interactiva (6.3-6.7): verificadas por trazabilidad de código contra los escenarios de spec + typecheck estricto + build + smoke HTTP del contrato. La prueba interactiva final en navegador (clic real sobre badge/modal) queda como pase rápido del usuario con la app corriendo — no existe runner de frontend ni automatización de navegador en el proyecto.

## Files Changed — Slice 1 (Backend)

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

## Files Changed — Slice 2 (Frontend)

| File | Action | What Was Done |
|------|--------|---------------|
| `gimnasioReact/src/model/notifications.model.ts` | Modified | Interface Notification reemplazada (campos del nuevo contrato: id, tipo, titulo, mensaje, fecha, relacion_tipo, relacion_id, link, whatsapp_link, is_read, read_at, created_at) + UnreadCountResponse |
| `gimnasioReact/src/api/action/notifications.api.ts` | Modified | 4 funciones nuevas (getNotifications, getUnreadCount, markOneRead, markAllAsRead); llamadas legacy `/membership-notifications/` eliminadas |
| `gimnasioReact/src/components/headerNav/NotificationMenu.tsx` | Modified | Badge real (getUnreadCount), lectura por item, key={n.id}, iconos por tipo nuevo, polling 5 min con Promise.all, empty state nuevo, WhatsApp no lee |
| `gimnasioReact/src/pages/admin/notifications/NotificationsPage.tsx` | Modified | Lista desde getNotifications, botón de lectura individual, mark-all con toast de éxito, key={n.id}, link=notification.link, estados loading/error |
| `gimnasioReact/src/pages/admin/calendario/CalendarioPage.tsx` | Modified | Deep link `?evento=<id>` (useSearchParams + getEvento + setSelectedEvent), toast de error en 404, helper toCalendarEvent reutilizado |
| `openspec/changes/notificaciones-nivel1/tasks.md` | Modified | 4.1-6.7 marcadas `[x]` |
| `openspec/changes/notificaciones-nivel1/apply-progress.md` | Modified | Merge con avance del Slice 2 |

## Test Summary

- **Backend**: 103/103 tests OK (79 existentes + 24 nuevos) — sin cambios en Slice 2 (solo verificación de no-regresión)
- **Frontend**: `npx tsc -b` exit 0; `npm run build` OK (1292 módulos, 1m15s)
- **Smoke HTTP (runserver local)**: `/Notificaciones/no-leidas/` → 401 sin token; `/membership-notifications/` → 404; `/CalendarioEventos/1/` → 401 sin token
- **Lint**: `npx eslint` sobre los 5 archivos falla por dependencia corrupta pre-existente (`node_modules/@eslint/eslintrc/node_modules/globals/globals.json` no es JSON válido) — no relacionado con este cambio; lint no forma parte de la verificación requerida

## Deviations from Design

- **Slice 1**: None — implementation matches design.md exactly. Notes for clarity: `NotificationManager` es una clase con classmethods (no un Django model Manager) para evitar import circular; `NotificationViewSet` usa `ReadOnlyModelViewSet` (sin escritura expuesta); título de evento "Evento programado hoy" (design no fijó el string exacto).
- **Slice 2**: None — implementation matches design.md exactly. Notas: (1) el deep link se dispara en un `useEffect` propio de mount (no al final de `fetchData`) para no reabrir el modal tras editar/mover eventos; el escenario de spec "fetch after calendar load" describe el resultado observable (modal abierto con el evento traído por id), que se cumple. (2) La lectura por item del menú se dispara en el click del Link (además de navegar), como pedía el escenario "Click notification marks read"; el botón WhatsApp es hermano del Link y no dispara lectura.

## Issues Found

1. **Slice 1 (resolved)**: test data collision en el helper del ViewSet test (relacion_id bajos chocaban con EventoCalendario reales) — corregido con espacio de ids alto (100000+). Producción correcta.
2. **Slice 1 (WARNING, resuelto en Slice 2)**: frontend temporalmente roto entre PRs (llamaba endpoints legacy eliminados). Resuelto en este slice: todas las referencias a `/membership-notifications/` fueron removidas.
3. **Slice 1 (INFO)**: test DB es MySQL (IntegrityError confirma constraint en motor real); `date.today()` UTC verificado empíricamente.
4. **Slice 2 (WARNING — entorno, pre-existente)**: `node_modules` tiene corrupción de disco (historial del repo: commit e482236 "reinstalar tailwindcss corrupto por corrupcion de disco"); eslint no puede arrancar por `globals.json` corrupto. No bloquea tsc/build. Sugerencia: `npm ci`/reinstalar dependencias cuando haya oportunidad.
5. **Slice 2 (INFO)**: QA interactiva en navegador (6.3-6.7) verificada por código + build + smoke; pase visual final recomendado por el usuario con la app corriendo.

## Workload / PR Boundary

- Mode: chained PR slice (stacked-to-main), PR 2 of 2
- Work units: WU1 (model+api+menu+page, tasks 4.1-5.2), WU2 (deep link, task 5.3), WU3 (artefactos SDD)
- Boundary: starts at `2f5df0f` (post-slice-1), ends at los commits de este slice; archivos backend intactos en Slice 2 (solo verificación)
- Estimated review budget: Slice 2 ≈ 169 inserciones / 78 eliminaciones (5 archivos frontend) — por debajo del presupuesto de 400 líneas

## Commits Made — Slice 1 (Backend)

1. `8c4ac73` feat(notificaciones): modelo Notification persistente y generador idempotente — models.py, migration 0008, services/
2. `5de8321` feat(notificaciones): API de notificaciones y eliminacion de endpoints legacy — serializers.py, views.py, urls.py, tests.py

## Commits Made — Slice 2 (Frontend)

1. `67f4665` feat(notificaciones): migrar menu y pagina de notificaciones al nuevo API — notifications.model.ts, notifications.api.ts, NotificationMenu.tsx, NotificationsPage.tsx
2. `c25a99f` feat(notificaciones): deep link de calendario desde notificaciones de eventos — CalendarioPage.tsx
3. `33881da` docs(sdd): registrar avance del cambio notificaciones-nivel1 (slice 2) — tasks.md, apply-progress.md

(No AI attribution, conventional commits en español, repo convention.)

## Estado acumulado

- **Tareas**: 28/28 completas (1.1-3.8 backend + 4.1-6.7 frontend) — change listo para `sdd-verify`
- **Backend suite**: 103/103 OK
- **Frontend**: tsc -b y build OK