# Tasks: Phase 1 Core Hardening

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 250–350 |
| 400-line budget risk | Medium |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Tasks 1–3) → PR 2 (Tasks 4–5) → PR 3 (Tasks 6–8) |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: Medium

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | CI infra + bug fixes (Tasks 1–3) | PR 1 | `python manage.py test gimnasioApp` | Full test suite on SQLite | settings.py, serializers.py, models.py (notified_at), ci.yml |
| 2 | Tenant safety + country code (Tasks 4–5) | PR 2 | `python manage.py test gimnasioApp` | Manager filtering + migration apply | models.py (ActiveManager, country_code), notifications.py |
| 3 | Audit + E2E test + soft delete (Tasks 6–8) | PR 3 | `python manage.py test gimnasioApp` | Registration endpoint + cancel flow | views.py, tests.py, frontend files |

## Phase 1: Foundation / Infrastructure

- [x] 1.1 Add `DATABASES['default']['TEST']` dict to `gimnasio/settings.py` with SQLite in-memory engine
- [x] 1.2 RED: Write test asserting `settings.DATABASES['default']['TEST']['ENGINE'] == 'django.db.backends.sqlite3'`
- [x] 1.3 GREEN: Confirm `python manage.py test gimnasioApp` passes on SQLite in <10s
- [x] 1.4 Create `.github/workflows/ci.yml` (ubuntu-latest, Python 3.12, `python manage.py test gimnasioApp`, SECRET_KEY + empty DATABASE_URL env)
- [x] 1.5 Verify CI workflow runs without MySQL service

## Phase 2: Bug Fixes

- [x] 2.1 Add `coerce_to_string=False` to `retencion_promedio` in `gimnasioApp/serializers.py` (line ~456)
- [x] 2.2 RED: Write test asserting `isinstance(data['retencion_promedio'], (int, float))` for platform stats endpoint
- [x] 2.3 GREEN: Confirm serializer returns number type; run `python manage.py test gimnasioApp`
- [x] 2.4 Remove `.toFixed(1)` workaround in `gimnasioReact/src/pages/admin/platform/PlatformDashboardPage.tsx` (line ~144), display `stats.retencion_promedio` directly
- [x] 3.1 Remove `notified_at` field from `MembresiaAsignada` in `gimnasioApp/models.py` (line ~182)
- [x] 3.2 RED: Write test asserting `MembresiaAsignada` has no `notified_at` attribute
- [x] 3.3 GREEN: Run `python manage.py makemigrations gimnasioApp` and verify `RemoveField` migration generated
- [x] 3.4 Run `python manage.py migrate gimnasioApp` and confirm migration applies cleanly
- [x] 3.5 Grep codebase for remaining `notified_at` references; confirm zero hits outside tests

## Phase 3: Core Implementation

- [x] 4.1 Add `ActiveManager` class to `gimnasioApp/models.py` filtering `is_active=True`
- [x] 4.2 Set `objects = ActiveManager()` and `all_objects = models.Manager()` on `Gimnasio`
- [x] 4.3 Set `objects = ActiveManager()` and `all_objects = UserManager()` on `Usuario`
- [x] 4.4 RED: Write test creating active + inactive Gym; assert `Gimnasio.objects.all()` excludes inactive, `all_objects` returns all
- [x] 4.5 GREEN: Confirm manager filtering tests pass; run `python manage.py test gimnasioApp`
- [x] 4.6 Audit `gimnasioApp/admin.py` — update admin classes to use `all_objects` where full visibility is needed
- [x] 4.7 Audit `gimnasioApp/views.py` — verify `PlatformStatsView` (line ~998) does not double-filter `is_active`
- [x] 5.1 Add `country_code = models.CharField(max_length=5, default='57', blank=True)` to `Gimnasio` in `gimnasioApp/models.py`
- [x] 5.2 RED: Write test asserting default is '57' and custom code ('1') is preserved
- [x] 5.3 GREEN: Run `python manage.py makemigrations gimnasioApp`; verify `AddField` migration generated
- [x] 5.4 Run `python manage.py migrate gimnasioApp` and confirm migration applies with default
- [x] 5.5 Update `NotificationManager._construir_whatsapp_link()` in `gimnasioApp/services/notifications.py` to accept `country_code` parameter (default '57')
- [x] 5.6 Update `_crear_membresia` call to pass `gimnasio.country_code` to `_construir_whatsapp_link`
- [x] 5.7 RED: Write test mocking phone; assert WhatsApp link uses provided country code prefix
- [x] 5.8 GREEN: Confirm WhatsApp link tests pass; run `python manage.py test gimnasioApp`

## Phase 4: Audit / Documentation

- [x] 6.1 Add docstring to `RegisterViewSet` in `gimnasioApp/views.py` with INTENTIONAL flag, threat model, and protections
- [x] 6.2 RED: Write test asserting `'INTENTIONAL' in RegisterViewSet.__doc__`
- [x] 6.3 GREEN: Confirm docstring test passes; run `python manage.py test gimnasioApp`

## Phase 5: Testing

- [x] 7.1 Add `ForcedPasswordChangeE2ETest` class to `gimnasioApp/tests.py`
- [x] 7.2 Implement admin scenario: create user with `must_change_password=True`, login → 403 → change password → 200
- [x] 7.3 Implement recepcion scenario: same flow with recepcion role
- [x] 7.4 RED: Write both test methods; confirm they fail (endpoint doesn't enforce yet — test documents expected behavior)
- [x] 7.5 GREEN: Run `python manage.py test gimnasioApp` — confirm tests pass against existing enforced flow

## Phase 6: New Feature — Soft Delete

- [x] 8.1 Add `('cancelada', 'Cancelada')` to `DemoRequest.ESTADOS` in `gimnasioApp/models.py`
- [x] 8.2 Add `destroy()` method to `DemoRequestViewSet` in `gimnasioApp/views.py` — set `estado='cancelada'`, save, return updated object
- [x] 8.3 Add `'delete'` to `http_method_names` on `DemoRequestViewSet`
- [x] 8.4 Add `validate_estado` to `DemoRequestSerializer` in `gimnasioApp/serializers.py` — reject modification of cancelled requests
- [x] 8.5 RED: Write unit test asserting `destroy()` sets `estado='cancelada'` and record persists in DB
- [x] 8.6 RED: Write unit test asserting second cancel returns 400
- [x] 8.7 RED: Write unit test asserting PATCH on cancelled request returns 400 (serializer validation)
- [x] 8.8 GREEN: Run `python manage.py test gimnasioApp` — all soft delete tests pass
- [x] 8.9 Add `deleteDemoRequest` function to `gimnasioReact/src/api/action/demoRequests.api.ts`
- [x] 8.10 Add delete button + confirmation modal to `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx` (show for pendiente/contactado states only)
- [x] 8.11 Verify frontend builds: `npm run build` in `gimnasioReact/`
