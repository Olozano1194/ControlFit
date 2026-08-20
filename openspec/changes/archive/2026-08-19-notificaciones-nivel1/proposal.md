# Proposal: notificaciones-nivel1 — Persistent Notification Foundation

## Intent

Staff notifications today are ephemeral and unreliable: recomputed per request over `MembresiaAsignada`, read-state coupled to the domain object (`notified_at`), gone once read. There is no per-item read, no unread count, no history; the badge shows raw list length; every membership notification link 404s (detail route removed in `23864ed`); calendar events produce zero reminders even though `relacion_tipo/relacion_id` are stored. Nivel 1 replaces the computed-on-demand system with a persistent, multi-tenant `Notification` model — idempotent generation (membership expirations + same-day event reminders), a real ViewSet API, and a frontend (bell menu + page + calendar deep links) that finally works. This is the foundation Nivel 2 (client-facing, auto-sending) builds on.

## Current State / Gap

- Backend: 2 function-based endpoints (`views.py:715,808`; `urls.py:31-32`), **zero tests** (0/79), unpaginated, unordered by recency, unbounded; bulk all-or-nothing read; dead code `numero_gimnasio`/`WHATSAPP_NUMBER` (`views.py:719`).
- Frontend: badge = `notifications.length`; React keys by index; membership links → Error404 (only `asignar-membresia-list` route exists); no per-item read; `getEvento(id)` exists but unused.

## Proposed Approach

1. **`Notification` model** (`gimnasioApp/models.py`): `gimnasio` FK, `tipo` (`por_vencer|vencida|evento`), `titulo`, `mensaje`, `fecha`, polymorphic `relacion_tipo`/`relacion_id`, `link`, `whatsapp_link`, `is_read`, `read_at`, `created_at`; **`UniqueConstraint(gimnasio, relacion_tipo, relacion_id, tipo)`** = idempotency key.
2. **Lazy idempotent generation**: `NotificationManager.generate_for_gimnasio()` with `get_or_create`, invoked inside the list endpoint (no Celery/cron exists). Sources: memberships (existing ≤3d / expired filters, now persisted) + events with `fecha_inicio__date=today` (same-day window, confirmed). Optional `generate_notifications` management command (pattern: `management/commands/`).
3. **API** — `NotificationViewSet` (`MultiTenantViewSetMixin`, `IsRecepcionUser`), router basename `Notificaciones`: GET list (triggers generation; **returns unread only** — read items disappear per UX), POST `{id}/marcar-leida/`, POST `marcar-todas-leidas/`, GET `no-leidas/` → `{count}`.
4. **Legacy endpoints removed** (not wrapped): both consumers are rewired in this same change; keeps one source of truth and avoids drift with deprecated `notified_at`.
5. **`notified_at` kept but deprecated** (help_text) — no destructive migration; cleanup = follow-up change.
6. **Frontend**: new `Notification` model/API client; NotificationMenu real badge (poll stays 5 min) + per-item read; NotificationsPage per-item read + mark-all + stable `key={id}`; membership link → `asignar-membresia-list`; CalendarioPage deep link `?evento=<id>` → existing detail modal via `getEvento(id)`.

## Scope

**In**: model+migration; generation manager; ViewSet + 4 endpoints; remove legacy; backend tests (idempotency, multi-tenant isolation, permissions, generation, read actions); frontend model/API/menu/page/deep-link/link-fix.
**Out**: auto WhatsApp/email (manual `wa.me` stays); real-time push; client notifications (Nivel 2); multi-day/configurable windows; read-history UI; retention jobs; dropping `notified_at` column; event-move stale-reminder invalidation; manual notification creation.

## Capabilities

- **New `notificaciones`**: model, generation, read lifecycle, API.
- **New `notificaciones-frontend`**: menu, page, client model/API.
- **Modified `calendario-eventos-frontend`**: deep-link requirement (`?evento=<id>` opens detail modal).

## Key Decisions

| Decision | Choice | Rationale |
|---|---|---|
| Generation trigger | Lazy in list endpoint | No Celery/cron in project; bounded windows, single-digit rows |
| Source ref | Polymorphic `relacion_tipo/id` | Matches `EventoCalendario` convention; one unique key; rows self-contained → orphans harmless |
| Legacy endpoints | Remove | Frontend rewired same change; single source of truth |
| Event window | Same day (`__date=today`) | Confirmed business decision |
| List semantics | Unread only | Confirmed: read notifications disappear |
| Polling | Keep 5 min | No product need for faster |

**Assumption**: previously-dismissed expirations reappear unread once after deploy (backfill semantics) — accepted.

## Affected Areas

| Area | Impact | Change |
|---|---|---|
| `gimnasioApp/models.py` | Modified | +`Notification` + manager; deprecate `notified_at` help_text |
| `gimnasioApp/migrations/` | New | Notification migration |
| `gimnasioApp/serializers.py`, `views.py`, `urls.py` | Modified | +ViewSet; remove legacy endpoints (views.py:715-832, urls.py:31-32) |
| `gimnasioApp/tests.py` | Modified | +notification test classes |
| `gimnasioReact/src/model/notifications.model.ts`, `api/action/notifications.api.ts` | Modified | New contract + 4 API calls |
| `NotificationMenu.tsx`, `NotificationsPage.tsx` | Modified | Real badge, per-item read, stable keys, link fix |
| `CalendarioPage.tsx` | Modified | `?evento=<id>` deep link |

## Risks

| Risk | Level | Mitigation |
|---|---|---|
| Stale reminder if event moves (unique key blocks regen) | MED | Accepted for Nivel 1; invalidation deferred |
| Dismissed expirations reappear once post-deploy | LOW | Documented; one-time |
| Generation latency on list | LOW | Bounded windows |
| **Review workload**: ~650-800 changed lines (backend ~350-450 + frontend ~250-350) — 400-line budget risk **High**; **Chained PRs recommended: Yes** (slice 1 backend, slice 2 frontend); **Decision needed before apply: Yes** (delivery strategy) | MED | sdd-tasks chains; backend slice is autonomously shippable |
| Frontend untested (no runner) | INFO | tsc -b + build + manual QA (project norm) |
| Hardcoded `57` wa.me prefix | INFO | Preserve; parameterize later |

## Rollback Plan

`git revert` the change: drop migration, restore legacy endpoints/views; frontend revert restores old API calls. No destructive migration, no data loss (new rows orphaned, harmless).

## Dependencies

- Django 5.2 / DRF patterns already in repo (Mixin, permissions, router). No new packages.

## Success Criteria

- [ ] Badge shows real unread count; read items vanish on read; links resolve (no 404).
- [ ] Same-day event reminders appear; membership expiring/expired notifications persist once (idempotent).
- [ ] `python manage.py test gimnasioApp` green (79 existing + new); `python manage.py check` passes; `tsc -b` + `npm run build` pass.
