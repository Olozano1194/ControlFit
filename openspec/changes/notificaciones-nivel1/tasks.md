# Tasks: notificaciones-nivel1 — Persistent Notification Foundation

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 550-700 (backend ~300-380, frontend ~250-320) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (backend) → PR 2 (frontend) |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Backend: model, migration, service, serializer, ViewSet, urls, legacy removal, tests | PR 1 | `python manage.py test gimnasioApp` | N/A (unit tests only) | All backend files; `git revert` removes model, migration, service, ViewSet, restores legacy endpoints |
| 2 | Frontend: model, API client, NotificationMenu, NotificationsPage, calendar deep link | PR 2 | `tsc -b && npm run build` | Manual QA: badge, per-item read, membership link, deep link | All frontend files; `git revert` restores old components |

---

## Phase 1: Backend Foundation (Model + Migration)

- [x] 1.1 Add `Notification` model to `gimnasioApp/models.py` — fields: gimnasio FK, tipo (choices), titulo, mensaje, fecha, relacion_tipo, relacion_id, link, whatsapp_link, is_read, read_at, created_at; UniqueConstraint(gimnasio, relacion_tipo, relacion_id, tipo); db_table='notification'; ordering=['-created_at']
- [x] 1.2 Generate migration `gimnasioApp/migrations/000X_notification.py` via `python manage.py makemigrations gimnasioApp`
- [x] 1.3 Run migration `python manage.py migrate` and verify with `python manage.py check`

## Phase 2: Backend Core Implementation (Service + Serializer + ViewSet)

- [x] 2.1 Create `gimnasioApp/services/__init__.py` (empty)
- [x] 2.2 Create `gimnasioApp/services/notifications.py` with `NotificationManager.generate_for_gimnasio(gimnasio)` — three get_or_create branches: expiring memberships (dateFinal > today, ≤ today+3d → tipo='por_vencer'), expired memberships (dateFinal ≤ today → tipo='vencida'), same-day events (fecha_inicio__date=today → tipo='evento'); Spanish titulo/mensaje; whatsapp_link with hardcoded 57 prefix; link → `/dashboard/asignar-membresia-list`
- [x] 2.3 Add `NotificationSerializer` to `gimnasioApp/serializers.py` — fields: id, tipo, titulo, mensaje, fecha, relacion_tipo, relacion_id, link, whatsapp_link, is_read, read_at, created_at; read_only: id, gimnasio, is_read, read_at, created_at
- [x] 2.4 Add `NotificationViewSet` to `gimnasioApp/views.py` — inherits MultiTenantViewSetMixin; permission_classes=[IsAuthenticated, IsRecepcionUser]; 4 actions: list (triggers generate, returns unread only, ordered -created_at), marcar_leida (POST, sets is_read+read_at), marcar_todas_leidas (POST, bulk update), no_leidas (GET, returns count)
- [x] 2.5 Update `gimnasioApp/urls.py` — import NotificationViewSet; register in router basename='Notificaciones'; remove legacy path entries (L31-32: membership_notifications and mark_notifications_read)
- [x] 2.6 Remove legacy views from `gimnasioApp/views.py` — delete membership_notifications function (L713-803) and mark_notifications_read function (L806-832); remove unused imports if any

## Phase 3: Backend Testing

- [x] 3.1 Test idempotency: create notification, call generate again, assert count unchanged (NotificationManager unit test)
- [x] 3.2 Test multi-tenant isolation: create notifications for gym A, query as gym B, assert empty
- [x] 3.3 Test permission enforcement: unauthenticated → 401; non-admin/recepcion → 403
- [x] 3.4 Test read state: per-item read sets is_read+read_at; bulk read marks all; unread count reflects changes
- [x] 3.5 Test generation triggers: list endpoint creates notifications for qualifying memberships/events
- [x] 3.6 Test generation edge cases: empty gym, no qualifying data, already-read items excluded from list
- [x] 3.7 Test legacy endpoint removal: GET `/membership-notifications/` → 404
- [x] 3.8 Run full test suite: `python manage.py test gimnasioApp` — all existing 79 + new tests pass

## Phase 4: Frontend Foundation (Model + API Client)

- [ ] 4.1 Replace `gimnasioReact/src/model/notifications.model.ts` — new interface with id, tipo ('por_vencer'|'vencida'|'evento'), titulo, mensaje, fecha, relacion_tipo, relacion_id, link, whatsapp_link, is_read, read_at, created_at
- [ ] 4.2 Replace `gimnasioReact/src/api/action/notifications.api.ts` — 4 functions: getNotifications(), getUnreadCount() → {count}, markOneRead(id), markAllAsRead()

## Phase 5: Frontend Core Implementation (Components)

- [ ] 5.1 Update `gimnasioReact/src/components/headerNav/NotificationMenu.tsx` — use getUnreadCount() for badge (not list length); per-item read via markOneRead(id) on click; stable key=n.id; new icon mapping (por_vencer→RiInformationLine yellow, vencida→RiCloseLine red, evento→RiCheckLine green); keep 5-min polling; empty state "No hay notificaciones nuevas"
- [ ] 5.2 Update `gimnasioReact/src/pages/admin/notifications/NotificationsPage.tsx` — use getNotifications(); per-item read button; markAllAsRead(); stable key=n.id; link field → notification.link (fixes membership link to /dashboard/asignar-membresia-list); loading/error states
- [ ] 5.3 Update `gimnasioReact/src/pages/admin/calendario/CalendarioPage.tsx` — read `?evento=<id>` from useSearchParams on mount; if present, call getEvento(id) and set selectedEvent to open detail modal; error toast on 404; import getEvento from calendario.api.ts

## Phase 6: Frontend Verification

- [ ] 6.1 Run `tsc -b` in gimnasioReact — TypeScript compilation passes with no errors
- [ ] 6.2 Run `npm run build` in gimnasioReact — production build succeeds
- [ ] 6.3 Manual QA: badge shows unread count, not list length
- [ ] 6.4 Manual QA: click notification → disappears, badge decrements
- [ ] 6.5 Manual QA: membership notification link navigates to /dashboard/asignar-membresia-list (no 404)
- [ ] 6.6 Manual QA: calendar deep link ?evento=<id> → modal opens with correct event
- [ ] 6.7 Manual QA: calendar deep link ?evento=999 → error toast, calendar loads normally

## Requirement Traceability

| Requirement | Tasks |
|-------------|-------|
| Notification Model | 1.1, 1.2, 1.3 |
| Idempotent Generation | 2.2, 3.1, 3.5 |
| Notification Read State | 2.4, 3.4 |
| Multi-Tenant Isolation | 2.4, 3.2 |
| Permission Enforcement | 2.4, 3.3 |
| API Endpoints | 2.4, 2.5, 2.6, 3.7 |
| Notification Content | 2.2 |
| Known Limitations | 3.6 (edge cases) |
| Frontend Model/API Client | 4.1, 4.2 |
| NotificationMenu Real Badge | 5.1, 6.3 |
| NotificationMenu Per-Item Read | 5.1, 6.4 |
| NotificationsPage List | 5.2 |
| Membership Link Fix | 2.2, 5.2, 6.5 |
| Calendar Deep Link | 5.3, 6.6, 6.7 |
| Loading/Error States | 5.1, 5.2 |
| Polling Cadence | 5.1 |
