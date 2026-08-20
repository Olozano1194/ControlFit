# Exploration: notificaciones-nivel1

Persistent, domain-driven notification foundation + calendar integration.
Nivel 1 (agreed): replace the computed-on-demand notification system with a
persistent `Notification` model (multi-tenant), idempotent generation from
membership expirations and calendar event reminders, list/mark-read/unread-count
endpoints, and a frontend (bell menu + notifications page) backed by the model.
Deferred: automatic WhatsApp/email sending (manual `wa.me` links stay).

---

## Current State

### Backend — notification endpoints (function-based, no model)

**`membership_notifications`** — `gimnasioApp/views.py:713-803`, `@api_view(['GET'])`,
`permission_classes = [IsAuthenticated]` (any authenticated role, incl. recepcion).

Two computed buckets over `MembresiaAsignada`, always filtered
`miembro__gimnasio=request.gimnasio`:
- **Expiring**: `dateFinal__gt=today AND dateFinal__lte=today+3 AND notified_at__isnull=True`
- **Expired**: `dateFinal__lte=today AND notified_at__isnull=True`

`select_related('miembro', 'membresia', 'miembro__gimnasio')`. Returns a plain list of
dicts (no pagination, ordering follows model default `-dateInitial`, NOT date-consistent):

```json
{
  "type": "warning" | "danger",
  "title": "Membresía próxima a expirar" | "Membresía vencida",
  "message": "La membresía de {member} - {plan} expirará en {n} días." | "... ya venció.",
  "date": "DD/MM/YYYY",
  "link": "/dashboard/asignar-membresia/{membership.id}/",
  "whatsapp_link": "https://wa.me/{phone}?text={urlencoded}",
  "membership_id": 123
}
```

WhatsApp link: phone digits only (`miembro.phone`, max_length=10), hardcoded `57`
country-code prefix, hardcoded URL-encoded Spanish message.
**Dead code**: `numero_gimnasio = getattr(settings, 'WHATSAPP_NUMBER', ...)` (views.py:719)
is computed and NEVER used — the gym-level WhatsApp number is ignored.

**`mark_notifications_read`** — `views.py:806-832`, `@api_view(['POST'])`, `IsAuthenticated`.
Bulk `.update(notified_at=timezone.now())` on both buckets. All-or-nothing: no per-item
granularity, no unread-count endpoint, no history (once read, gone forever).

URLs (not in router): `/gym/api/v1/membership-notifications/` and
`/gym/api/v1/membership-notifications/read/` (`urls.py:31-32`).

**Test coverage: ZERO.** Of the 79 backend tests, none touch these endpoints or
`notified_at`.

### Backend — models

- `MembresiaAsignada` (`models.py:168`) — `gimnasio` FK (direct), `miembro` FK → `UsuarioGym`
  (`related_name='miembro'`), `membresia` FK, `multiplier`, `discount_percent`, `dateInitial`,
  `dateFinal` (computed, `editable=False`), `price` (computed), `created_at`,
  **`notified_at`** (`DateTimeField null=True`, `models.py:178`) — the current read-state
  source of truth, stored ON the domain object (coupling).
- Member model is **`UsuarioGym`** (`models.py:90`): `name`, `lastname`, `phone`
  (max_length=10), `address`, `gimnasio`, `created_at`. (Not `Miembro`.)
- Calendar (migration `0007_tipoevento_eventocalendario.py`, shipped and committed `da69a52`):
  - `TipoEvento` (`models.py:279`): `nombre`, `color`, `gimnasio`, `created_at`.
    Admin-only viewset.
  - `EventoCalendario` (`models.py:302`): `titulo`, `fecha_inicio`/`fecha_fin` (DateTimeField),
    `descripcion`, `tipo` FK → TipoEvento (`SET_NULL`, nullable), `relacion_tipo`
    (CharField(50), nullable — polymorphic relation convention), `relacion_id`
    (IntegerField, nullable), `created_by` FK → Usuario (`SET_NULL`), `gimnasio`,
    `created_at`. **`relacion_tipo`/`relacion_id` are stored but never interpreted** —
    perfect anchor for linking events to domain objects later.

### Backend — API patterns

- **Multi-tenancy**: `MultiTenantViewSetMixin` (`mixins.py`) — `get_queryset` filters
  `gimnasio=self.request.gimnasio` (or nested via `gimnasio_field`, e.g.
  `'miembro__gimnasio'` used by `MembresiaAsignadaViewSet`), `perform_create`/`perform_update`
  save `gimnasio=self.request.gimnasio`. `GimnasioMiddleware` sets `request.gimnasio` from
  the authenticated user or the JWT Bearer token. Default permission `IsAuthenticated`.
- **Permissions** (`permissions.py`): `IsAdminUser` (admin only), `IsRecepcionUser`
  (admin+recepcion, recepcion cannot DELETE), `IsOwnerOrAdmin`. Convention:
  viewsets combine `[IsAuthenticated, <role-permission>]`.
- **Router**: `DefaultRouter` in `urls.py` with English/Spanish mixed basenames
  (`UserGym`, `MemberShips`, `TiposEvento`, `CalendarioEventos`).
- **Serializers**: ModelSerializer, `gimnasio` in `read_only_fields`, nested `_details`
  style (`miembro_details`, `tipo_detalle`), custom `create()` pulling
  `gimnasio = getattr(request, 'gimnasio', None)` for non-mixin flows.
- `EventoCalendarioViewSet` (`views.py:845`): `IsRecepcionUser`, `perform_create` saves
  `gimnasio + created_by`, `?start=&end=` overlap filter. `TipoEventoViewSet`: admin only.

### Frontend — notifications

- `src/model/notifications.model.ts` — `Notification { type, title, message, date, link,
  whatsapp_link?, membership_id? }`. **No `id`, no `is_read`, no `created_at`** — cannot
  key rows reliably (menu keys by index, page keys by `membership_id` which is undefined
  for future types).
- `src/api/action/notifications.api.ts` — `getMemberNotifications()` → GET
  `/membership-notifications/`; `markNotificationsAsRead()` → POST
  `/membership-notifications/read/`.
- `NotificationMenu.tsx` (bell, rendered in `NavHeader.tsx:28`) — fetch on mount +
  **polling every 5 minutes** (`5 * 60 * 1000`), badge = `notifications.length` (not an
  unread count), "Marcar como leídas" clears the whole list after calling the API,
  per-item `Link` + optional wa.me button, footer link → `/dashboard/notifications`.
- `NotificationsPage.tsx` (`/dashboard/notifications` route, `App.tsx:61`) — fetch on mount
  (no polling), "Marcar todas como leídas", no per-item read actions, no pagination.

### Frontend — calendar integration points

- Route `/dashboard/calendar` → `CalendarioPage` (`App.tsx:63`); sidebar entries for BOTH
  roles (`SideBarAdmin.tsx:78`, `SideBarUser.tsx:75` — recepcion link fixed in a3deb05).
- `CalendarioPage.tsx` (399 lines, fully wired after a3deb05/c33c7bd): RBC month/week/day/
  agenda, DnD for admin (`patchEvento`), detail modal with Editar/Eliminar, `EventoForm`
  modal, `TipoEventoAdmin` modal. **No deep-linkable event detail route** — detail is
  modal state (`selectedEvent`). `getEvento(id)` API exists (`calendario.api.ts:50`) but is
  currently unused — ready to power `?evento=<id>` deep links.
- `calendario.model.ts` / `calendario.api.ts`: full contract (`EventoCalendario`, CRUD +
  PATCH + public endpoint).

### Dead link (pre-existing bug)

Notification `link` is `/dashboard/asignar-membresia/{id}/`, but the only matching route in
`App.tsx` is `asignar-membresia-list` — the detail/form route was removed in `23864ed`
("eliminar formulario duplicado, módulo queda solo con listado"). **Clicking any current
membership notification → Error404.**

---

## Problems / Gaps

1. **Read state coupled to the domain object**: `notified_at` lives on `MembresiaAsignada`;
   notifications are recomputed on every request and disappear once read. No history, no
   per-item read, no unread count.
2. **Unbounded, unordered, unpaginated**: every never-read expired membership ever
   accumulates in the list; `dateFinal` ordering is not by notification recency.
3. **Zero test coverage** for the notification endpoints (0/79 tests).
4. **Badge is fake**: `count = notifications.length`, not unread semantics; on the page,
   "read" state only exists client-side after a bulk call.
5. **Dead code**: `numero_gimnasio`/`WHATSAPP_NUMBER` never used; hardcoded `57` country
   prefix; hardcoded Spanish wa.me message in the backend.
6. **Dead frontend links**: membership notification links 404 (route mismatch).
7. **No calendar reminders**: `EventoCalendario.relacion_tipo/relacion_id` exist but nothing
   consumes them; gym staff get zero heads-up for events.
8. **No stable id in the API shape** → React keys are index/`membership_id` (unreliable).
9. Frontend has no test runner — verification is `tsc -b` + `npm run build` + manual QA.

---

## Integration Points

| Point | How it plugs in |
|-------|-----------------|
| `EventoCalendario.relacion_tipo`/`relacion_id` | Polymorphic-relation convention already in the codebase; reuse for the Notification source reference (`relacion_tipo='membership'|'evento'`, `relacion_id=<pk>`) or use direct FKs — decision in proposal |
| `EventoCalendarioViewSet` pattern | Blueprint for the Notification viewset: `MultiTenantViewSetMixin` + `IsRecepcionUser` + `perform_create` extras + router registration |
| `getEvento(id)` (unused API) + `CalendarioPage` modal state | Deep link `/dashboard/calendar?evento=<id>` → auto-open detail modal |
| `MembresiaAsignada.dateFinal` | Generation source for expiry notifications (existing 3-day window + expired) |
| `NotificationMenu` polling + badge | Switch badge to real unread count endpoint; per-item read on click |
| Router basename convention | `/Notificaciones/` (Spanish, matching `TiposEvento`/`CalendarioEventos`) |
| `WHATSAPP_NUMBER` setting | Fix dead code: use gym-level number as fallback when building stored `whatsapp_link` (or drop it) |

---

## Proposed Nivel 1 Scope

### Suggested `Notification` model (fields)

- `gimnasio` FK (required) — multi-tenant, per `MultiTenantViewSetMixin` default.
- `tipo` — CharField choices: `('por_vencer', 'Membresía próxima a vencer')`,
  `('vencida', 'Membresía vencida')`, `('evento', 'Recordatorio de evento')`.
  Drives title + frontend icon mapping (`warning`/`danger`/`info` derived, or store
  `severity` separately — decision in design).
- `titulo` CharField, `mensaje` TextField, `fecha` DateField (display date; ISO in API).
- `relacion_tipo` CharField(50) nullable + `relacion_id` IntegerField nullable —
  polymorphic source reference (follows `EventoCalendario` convention); or two direct
  FKs (`membresia_asignada` SET_NULL, `evento` SET_NULL) — decision in design. Either way
  the idempotency key needs a unique constraint (below).
- `whatsapp_link` TextField nullable — generated once at creation (manual wa.me only),
  `link` (route) computed or stored.
- `is_read` BooleanField default False, `read_at` DateTimeField nullable.
- `created_at` auto_now_add.
- **Idempotency**: `UniqueConstraint(gimnasio, relacion_tipo, relacion_id, tipo)` —
  same source + same kind → one row forever. Membership renewal creates a NEW
  `MembresiaAsignada` row → new id → new notification. Same membership can legitimately
  produce both `por_vencer` and `vencida` (different `tipo`).

### Generation strategy (idempotent)

- `NotificationManager.generate_for_gimnasio(gimnasio)` using `get_or_create` against the
  unique constraint. Sources:
  - Memberships: same filters as today (expiring ≤ 3 days, expired), each producing its
    notification row if missing.
  - Events: `EventoCalendario` with `fecha_inicio` within a reminder window — default
    `[now, now + 24h]` (decision point; window constant in settings or module const).
- **Trigger**: no Celery/cron exists in this project. Cheapest robust option: generate
  lazily inside the list endpoint before returning (bounded: 3-day membership window +
  today's/tomorrow's events). Optional companion management command
  `python manage.py generate_notifications` for cron later.
- Backfill note: memberships already `notified_at`-read are treated as fresh sources —
  after deploy, previously dismissed expirations may reappear unread once. Acceptable;
  call out in proposal.

### Endpoints (new ViewSet, `MultiTenantViewSetMixin`, `IsRecepcionUser`)

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/gym/api/v1/Notificaciones/` | GET | List (triggers generation), ordered `-created_at`, optional `?no_leidas=true` |
| `/gym/api/v1/Notificaciones/` | POST | Manual notification (admin) — optional Nivel 1 |
| `/gym/api/v1/Notificaciones/{id}/marcar-leida/` | POST | Per-item read (custom action) |
| `/gym/api/v1/Notificaciones/marcar-todas-leidas/` | POST | Bulk read (custom action) |
| `/gym/api/v1/Notificaciones/no-leidas/` | GET | `{count}` for the badge (custom action) |

Legacy endpoints `membership-notifications/` + `read/` removed or left as thin wrappers —
decision in proposal (frontend switches fully).

### Frontend changes

- `notifications.model.ts` — new `Notification` interface: `id`, `tipo`, `titulo`,
  `mensaje`, `fecha`, `link`, `whatsapp_link?`, `relacion_tipo`, `relacion_id`, `is_read`,
  `read_at`, `created_at`.
- `notifications.api.ts` — `getNotifications()`, `getUnreadCount()`, `markOneRead(id)`,
  `markAllAsRead()` (replaces both legacy calls).
- `NotificationMenu.tsx` — badge = real unread count (poll stays 5 min; option: 1 min,
  decision in proposal); mark read on click; keep wa.me button; footer link unchanged.
- `NotificationsPage.tsx` — per-item read/unread UI + mark-all; stable `key={n.id}`;
  fix membership link → `/dashboard/asignar-membresia-list` (current 404).
- Calendar deep link — `CalendarioPage` reads `?evento=<id>` from URL, calls `getEvento(id)`,
  opens the existing detail modal (small diff; modal already supports `selectedEvent`).
- WhatsApp stays manual (no auto-send): links generated server-side at creation time.

### `notified_at` decision (recommendation)

**Keep the column in Nivel 1** (no destructive migration): stop writing it, mark deprecated
in the model help_text. Cleanup migration (drop column) as a separate follow-up change.
Rationale: zero-data-risk switch, no consumers after frontend moves to the new API.

### Tests (strict_tdd applies — backend)

- Model: unique constraint idempotency, `generate_for_gimnasio` creates once / no-dup,
  multi-tenant isolation (gym A rows never seen by gym B).
- API: permissions (admin + recepcion allowed; recepcion no DELETE if ModelViewSet used),
  list triggers generation, per-item read, bulk read, unread count, event reminder window,
  membership expiring/expired generation, cross-gym 404/empty.
- Frontend: no runner — `tsc -b` + `npm run build` + manual QA.

---

## Risks / Tolerance

| Risk | Level | Mitigation |
|------|-------|------------|
| Legacy links 404 after switch if any consumer remains | LOW | Frontend switches fully; grep confirms only 2 components consume the API |
| Previously-dismissed expirations reappear after deploy (backfill semantics) | LOW | Expected behavior change; document in proposal |
| Idempotency vs. moved events: if an event's date shifts after a reminder is created, the old reminder stays (unique key) | MED | Nivel 1 accepts stale reminder; delete-on-fecha-change deferred to Nivel 2 |
| Generation latency on list (get_or_create loop) | LOW | Bounded windows; single-digit rows typical per gym |
| Hardcoded country code `57` in wa.me links | INFO | Preserve current behavior; parameterize later |
| Line budget: backend (model+migration+serializer+viewset+urls+tests ~350-450) + frontend (~250-350) likely exceeds 400 | MED | `sdd-tasks` should forecast and likely chain: backend slice → frontend slice |
| Frontend has no tests | INFO | Verification = tsc + build + manual QA (project norm) |
| `WHATSAPP_NUMBER` dead code — decide reuse or drop | INFO | Fix while touching the generator |

---

## Out of Scope (Nivel 1)

- Automatic WhatsApp/email sending to members (WhatsApp stays manual wa.me links).
- Real-time push (WebSocket/SSE) — polling only.
- Notification preferences per gym/user, notification history retention/cleanup jobs.
- Event-move invalidation of stale reminders (Nivel 2).
- Dropping the `notified_at` column (follow-up cleanup change).
- Recepcion notification creation (optional, admin-only if included).

---

## Ready for Proposal

Yes. Proposal should confirm: (1) generation trigger = lazy inside list endpoint (+
optional management command), (2) event reminder window default 24h before start,
(3) polymorphic `relacion_tipo/relacion_id` vs direct FKs, (4) legacy endpoint
removal vs wrapper, (5) polling interval (5 min vs shorter), (6) `notified_at` kept
but deprecated, (7) chained PR forecast (backend slice, then frontend slice).
