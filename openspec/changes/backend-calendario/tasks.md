# Tasks: Backend Calendar Module (TipoEvento + EventoCalendario + Public Endpoint)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 350-420 (tests dominate, ~170 lines) |
| 400-line budget risk | Medium |
| Chained PRs recommended | No |
| Suggested split | Single PR (all tasks in one PR) |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Models + Migration | PR 1 | `python manage.py check` | `python manage.py makemigrations gimnasioApp` | `gimnasioApp/models.py`, new migration file |
| 2 | Serializers | PR 1 | `python manage.py test gimnasioApp` | N/A — unit tests validate serializer logic | `gimnasioApp/serializers.py` |
| 3 | ViewSets + URLs + Public Endpoint | PR 1 | `python manage.py test gimnasioApp` | N/A — integration tests validate viewsets | `gimnasioApp/views.py`, `gimnasioApp/urls.py` |
| 4 | Tests (TDD) | PR 1 | `python manage.py test gimnasioApp` | N/A — test runner validates all scenarios | `gimnasioApp/tests.py` |

---

## Phase 1: Foundation — Models + Migration

- [x] 1.1 Add `TipoEvento` model to `gimnasioApp/models.py` (nombre, color, gimnasio FK, created_at)
- [x] 1.2 Add `EventoCalendario` model to `gimnasioApp/models.py` (titulo, fecha_inicio, fecha_fin, descripcion, tipo FK nullable, relacion_tipo, relacion_id, created_by, gimnasio FK, created_at)
- [x] 1.3 Run `python manage.py makemigrations gimnasioApp` to generate migration
- [x] 1.4 Verify: `python manage.py check` passes

## Phase 2: Serializers

- [x] 2.1 Add `TipoEventoSerializer` to `gimnasioApp/serializers.py` (fields: id, nombre, color, gimnasio, created_at; read_only: id, gimnasio, created_at)
- [x] 2.2 Add `TipoEventoSimpleSerializer` to `gimnasioApp/serializers.py` (fields: id, nombre, color)
- [x] 2.3 Add `EventoCalendarioSerializer` to `gimnasioApp/serializers.py` (nested tipo_detalle, validate fecha_fin > fecha_inicio)

## Phase 3: ViewSets + URLs + Public Endpoint

- [x] 3.1 Add `TipoEventoViewSet` to `gimnasioApp/views.py` (MultiTenantViewSetMixin, ModelViewSet, IsAuthenticated + IsAdminUser)
- [x] 3.2 Add `EventoCalendarioViewSet` to `gimnasioApp/views.py` (MultiTenantViewSetMixin, ModelViewSet, IsAuthenticated + IsRecepcionUser, override perform_create + get_queryset with overlap filter)
- [x] 3.3 Add `PublicCalendarioView` to `gimnasioApp/views.py` (APIView, AllowAny, get_object_or_404, return events ordered by fecha_inicio)
- [x] 3.4 Register `TipoEventoViewSet` and `EventoCalendarioViewSet` in router in `gimnasioApp/urls.py`
- [x] 3.5 Register `PublicCalendarioView` at `api/calendario/publico/<int:gimnasio_id>/` in `gimnasioApp/urls.py` (NOT under /gym/api/v1/)
- [x] 3.6 Verify: `python manage.py check` passes

## Phase 4: Tests (TDD)

- [x] 4.1 Add `TipoEventoModelTest` to `gimnasioApp/tests.py` — required fields, gimnasio FK isolation
- [x] 4.2 Add `EventoCalendarioModelTest` to `gimnasioApp/tests.py` — nullable fields, fecha_fin > fecha_inicio validation
- [x] 4.3 Add `TipoEventoViewSetTest` to `gimnasioApp/tests.py` — admin-only CRUD, 403 for recepcion, cross-gym isolation
- [x] 4.4 Add `EventoCalendarioViewSetTest` to `gimnasioApp/tests.py` — CRUD with IsRecepcionUser, created_by auto-set, tipo_detalle nesting, nullable fields
- [x] 4.5 Add `RangeFilterTest` to `gimnasioApp/tests.py` — overlap semantics, non-overlapping exclusion, no-filter returns all
- [x] 4.6 Add `PublicCalendarioEndpointTest` to `gimnasioApp/tests.py` — valid gym returns events, 404 for unknown gym, 405 for non-GET, empty list for gym with no events
- [x] 4.7 Run `python manage.py test gimnasioApp` — all tests pass

## Phase 5: Integration Verification

- [x] 5.1 Run `python manage.py test gimnasioApp` — full suite passes
- [x] 5.2 Verify endpoints manually: `python manage.py runserver` and test CRUD + public endpoint
- [x] 5.3 Verify `python manage.py check` passes (no warnings)
