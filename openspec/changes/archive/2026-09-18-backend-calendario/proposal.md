# Proposal: Backend Calendar Module (TipoEvento + EventoCalendario + Public Endpoint)

## Intent

The frontend calendar module already implements and consumes the calendar API contract (`gimnasioReact/src/model/calendario.model.ts`, `gimnasioReact/src/api/action/calendario.api.ts`), but the backend has zero calendar support: no TipoEvento/EventoCalendario models and no endpoints (confirmed via git grep across all branches). The calendar screen cannot load events or event types. This change implements the missing backend slice so the existing frontend contract works.

## Scope

### In Scope
- Models `TipoEvento` (nombre, color) and `EventoCalendario` (titulo, fecha_inicio, fecha_fin, descripcion, tipo FK nullable, relacion_tipo/relacion_id optional, created_by nullable), both multi-tenant via `gimnasio` FK + `created_at`
- DB migration for both tables
- Serializers: `TipoEventoSerializer`, `TipoEventoSimpleSerializer` (nested `tipo_detalle`: id/nombre/color), `EventoCalendarioSerializer`
- Viewsets `TipoEventoViewSet` + `EventoCalendarioViewSet` (MultiTenantViewSetMixin), `?start=&end=` range filter
- Public endpoint `GET /api/calendario/publico/{gimnasio_id}/` (AllowAny, NOT under `/gym/api/v1`)
- Tests in `gimnasioApp/tests.py` (multi-tenant isolation, CRUD, nesting, range filter, public endpoint)

### Out of Scope
- Frontend changes (contract fixed, not touched)
- Polymorphic logic for `relacion_tipo`/`relacion_id` (stored as optional plain fields only)
- React form/UI wiring
- Public calendar page rendering (frontend concern)

## Capabilities

### New Capabilities
- `tipo-evento`: multi-tenant CRUD of calendar event types
- `evento-calendario`: multi-tenant CRUD of calendar events with nested `tipo_detalle` and start/end range filter
- `calendario-publico`: unauthenticated read-only public calendar endpoint by gimnasio id

### Modified Capabilities
- None (`openspec/specs/` is empty)

## Approach

Follow project conventions: `gimnasio` FK + related_name + `db_table` Meta + `created_at`; `MultiTenantViewSetMixin` (get_queryset filter + perform_create saves gimnasio); ModelViewSet with `IsRecepcionUser`; DefaultRouter registration; tests with APIRequestFactory + force_authenticate. `EventoCalendarioViewSet` overrides `perform_create` to also set `created_by=request.user`, and `get_queryset` to apply start/end overlap filter + order by fecha_inicio. Public endpoint: APIView with `AllowAny`, resolves Gimnasio from the URL kwarg (404 if missing), returns only that gym's events — never relies on `request.gimnasio` (anonymous requests).

## Affected Areas

| Path | Impact | Change |
|------|--------|--------|
| `gimnasioApp/models.py` | Modified | +2 models |
| `gimnasioApp/serializers.py` | Modified | +3 serializers |
| `gimnasioApp/views.py` | Modified | +2 viewsets, +1 APIView |
| `gimnasioApp/urls.py` | Modified | +2 router registrations, +1 public path |
| `gimnasioApp/migrations/000X_*.py` | New | 2 tables |
| `gimnasioApp/tests.py` | Modified | +calendar test classes |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Public endpoint leaks other gyms' events | Med | Strict filter by gimnasio_id kwarg; cross-gym isolation tests |
| Line budget near 400 (tests dominate) | Med | Keep tests focused on core scenarios; sdd-tasks may split PR slices |
| Range filter semantics mismatch | Low | Overlap semantics pinned in specs with Given/When/Then |
| Migration naming/ordering | Low | makemigrations generates it; `manage.py check` gates |

## Size Forecast

| Area | Est. lines (added) |
|------|--------------------|
| models.py | ~65 |
| serializers.py | ~55 |
| views.py | ~45 |
| urls.py | ~10 |
| migration | ~50 (generated) |
| tests.py | ~170 |
| **Total** | **~395** |

`Decision needed before apply: No` — `Chained PRs recommended: No` — `400-line budget risk: Medium` (borderline; tests dominate, sdd-tasks confirms split).

## Rollback Plan

`git revert` the feature commit, then `python manage.py migrate gimnasioApp <previous>` to drop both tables. Only new tables affected; no existing data risk.

## Dependencies

- None external. DB migration required before deploy.

## Success Criteria

- [ ] `python manage.py test gimnasioApp` passes (existing + new tests)
- [ ] `/gym/api/v1/TiposEvento/` CRUD scoped to the caller's gym only
- [ ] `/gym/api/v1/CalendarioEventos/` CRUD, `tipo_detalle` nested, `?start=&end=` filter works
- [ ] `created_by` auto-set to request.user; `tipo`/`relacion_*` nullable as contracted
- [ ] `GET /api/calendario/publico/{id}/` works unauthenticated, returns only that gym's events, 404 for unknown gym
- [ ] `python manage.py check` passes

## Proposal Question Round

Decisions confirmed by user:
1. Permissions: `TipoEventoViewSet` → admin-only; `EventoCalendarioViewSet` → `IsRecepcionUser` (admin + recepcion)
2. Range filter: overlap semantics (`fecha_inicio <= end AND fecha_fin >= start`)
3. Public endpoint: ALL events of the gym ordered by `fecha_inicio` (no future-only filter)
4. `fecha_inicio`/`fecha_fin` as `DateTimeField` (ISO datetimes)