# Tasks: tests-refactor

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 1500–2500 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 → PR 2 → PR 3 → PR 4 → PR 5 |
| Delivery strategy | ask-on-risk |
| Chain strategy | stacked-to-main |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: stacked-to-main
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Foundation: helpers, factories, conftest | PR 1 | `python -c "from gimnasioApp.tests.helpers import make_uploaded_image"` | N/A — import-only verification, no test execution needed | `tests/helpers.py`, `tests/factories.py`, `tests/conftest.py` |
| 2 | Independent modules: middleware, mixins, views | PR 2 | `python manage.py test gimnasioApp.tests.test_middleware gimnasioApp.tests.test_mixins gimnasioApp.tests.test_views` | Django TestCase suite | `tests/test_middleware.py`, `tests/test_mixins.py`, `tests/test_views.py` |
| 3 | Domain modules: storage, payments, membership, serializers, email | PR 3 | `python manage.py test gimnasioApp.tests.test_storage gimnasioApp.tests.test_payments gimnasioApp.tests.test_membership_models gimnasioApp.tests.test_serializers` | Django TestCase suite | `tests/test_storage.py`, `tests/test_payments.py`, `tests/test_membership_models.py`, `tests/test_serializers.py`, `tests/test_email.py` |
| 4 | Integration modules: JWT, CSRF, auth, token verify | PR 4 | `python manage.py test gimnasioApp` | Full Django test suite | `tests/test_jwt_token.py`, `tests/test_csrf_cookie.py`, `tests/test_csrf_validation.py`, `tests/test_auth_csrf.py`, `tests/test_token_verify.py`, `tests/test_csrf_enforcement.py` |
| 5 | Backward compat + cleanup | PR 5 | `python manage.py test gimnasioApp` + `pytest gimnasioApp/tests/` | Full dual-runner verification | `tests/__init__.py`, `tests.py` deletion |

## Phase 1: Foundation

- [x] 1.1 Create `gimnasioApp/tests/` package directory
- [x] 1.2 Create `gimnasioApp/tests/__init__.py` with empty content
- [x] 1.3 Create `gimnasioApp/tests/helpers.py` — extract `_make_uploaded_image()` and `_make_request_with_gym()` from `tests.py`, rename to public API (`make_uploaded_image`, `make_request_with_gym`)
- [x] 1.4 Create `gimnasioApp/tests/factories.py` — `create_gimnasio()`, `create_user()`, `create_admin_user()`, `create_miembro()`, `create_membresia()`, `create_membresia_asignada()`
- [x] 1.5 Create `gimnasioApp/tests/conftest.py` — pytest fixtures: `gimnasio` (session-scoped), `admin_user`, `miembro`, `membresia`, `membresia_asignada` (function-scoped)
- [x] 1.6 Verify foundation: `python -c "from gimnasioApp.tests.helpers import make_uploaded_image; print('OK')"`

## Phase 2: Independent Modules (no cross-dependencies)

- [x] 2.1 Create `gimnasioApp/tests/test_middleware.py` — extract `GimnasioMiddlewareTest` (lines 25–71), update imports to use `tests.factories`
- [x] 2.2 Verify: `python manage.py test gimnasioApp.tests.test_middleware`
- [x] 2.3 Create `gimnasioApp/tests/test_mixins.py` — extract `MultiTenantViewSetMixinTest` (lines 73–145), update imports to use `tests.factories`
- [x] 2.4 Verify: `python manage.py test gimnasioApp.tests.test_mixins`
- [x] 2.5 Create `gimnasioApp/tests/test_views.py` — extract `UserViewSetCreateTest` (lines 147–206), update imports to use `tests.factories`
- [x] 2.6 Verify: `python manage.py test gimnasioApp.tests.test_views`

## Phase 3: Domain Modules

- [x] 3.1 Create `gimnasioApp/tests/test_storage.py` — extract `SupabaseMediaStorageTest` (lines 208–251) and `UsuarioSerializerAvatarTest` (lines 253–364), replace `_make_uploaded_image` with `tests.helpers.make_uploaded_image`
- [x] 3.2 Verify: `python manage.py test gimnasioApp.tests.test_storage`
- [x] 3.3 Create `gimnasioApp/tests/test_integration_avatar.py` — extract `AvatarUploadIntegrationTest` (lines 366–421), update imports
- [x] 3.4 Verify: `python manage.py test gimnasioApp.tests.test_integration_avatar`
- [x] 3.5 Create `gimnasioApp/tests/test_payments.py` — extract `MembresiaAsignadaSaveTest` (lines 423–479), `PagoMembresiaValidacionTest` (lines 481–585), `MembresiaAsignadaPropiedadesTest` (lines 587–647), `PagoMembresiaIntegracionTest` (lines 649–725), refactor `setUp()` to use factories
- [x] 3.6 Verify: `python manage.py test gimnasioApp.tests.test_payments`
- [x] 3.7 Create `gimnasioApp/tests/test_home_dashboard.py` — extract `HomeDashboardPagosTest` (lines 727–820), refactor `setUp()` to use factories
- [x] 3.8 Verify: `python manage.py test gimnasioApp.tests.test_home_dashboard`
- [x] 3.9 Create `gimnasioApp/tests/test_membership_models.py` — extract `MembresiaModelTest` (lines 822–877), `MembresiaAsignadaModelSaveTest` (lines 879–941), `SeedDefaultMembershipsTest` (lines 943–1014), refactor `setUp()` to use factories
- [x] 3.10 Verify: `python manage.py test gimnasioApp.tests.test_membership_models`
- [x] 3.11 Create `gimnasioApp/tests/test_serializers.py` — extract `MembresiasSerializerTest` (lines 1016–1077), `MembresiaAsignadaSerializerValidationTest` (lines 1079–1127), refactor `setUp()` to use factories
- [x] 3.12 Verify: `python manage.py test gimnasioApp.tests.test_serializers`
- [x] 3.13 Create `gimnasioApp/tests/test_email.py` — extract `EmailServiceTest` (lines 1129–1261), update imports
- [x] 3.14 Verify: `python manage.py test gimnasioApp.tests.test_email`

## Phase 4: Integration Modules

- [x] 4.1 Create `gimnasioApp/tests/test_jwt_token.py` — extract `TokenLifetimeSettingsTest` (lines 1263–1297), update imports
- [x] 4.2 Verify: `python manage.py test gimnasioApp.tests.test_jwt_token`
- [x] 4.3 Create `gimnasioApp/tests/test_csrf_cookie.py` — extract `CSRFSettingTest` (lines 1299–1311) and `CSRFCookieHelperTest` (lines 1313–1395), update imports
- [x] 4.4 Verify: `python manage.py test gimnasioApp.tests.test_csrf_cookie`
- [x] 4.5 Create `gimnasioApp/tests/test_csrf_validation.py` — extract `CSRFValidationTest` (lines 1397–1497), update imports
- [x] 4.6 Verify: `python manage.py test gimnasioApp.tests.test_csrf_validation`
- [x] 4.7 Create `gimnasioApp/tests/test_auth_csrf.py` — extract `AuthViewsCSRFCookieTest` (lines 1499–1594), update imports
- [x] 4.8 Verify: `python manage.py test gimnasioApp.tests.test_auth_csrf`
- [x] 4.9 Create `gimnasioApp/tests/test_token_verify.py` — extract `TokenVerifyEndpointTest` (lines 1596–1734) and `TokenVerifyIntegrationTest` (lines 1736–1830), update imports
- [x] 4.10 Verify: `python manage.py test gimnasioApp.tests.test_token_verify`
- [x] 4.11 Create `gimnasioApp/tests/test_csrf_enforcement.py` — extract `CSRFEnforcementIntegrationTest` (lines 1832–1937) and `FullAuthFlowIntegrationTest` (lines 1939–2015), update imports
- [x] 4.12 Verify: `python manage.py test gimnasioApp.tests.test_csrf_enforcement`

## Phase 5: Backward Compatibility & Cleanup

- [x] 5.1 Update `gimnasioApp/tests/__init__.py` — add explicit re-exports for all 26 test classes
- [x] 5.2 Verify backward compat: `python -c "from gimnasioApp.tests import GimnasioMiddlewareTest; print('OK')"`
- [x] 5.3 Verify no duplicate helpers: `rg "_make_uploaded_image|_make_request" gimnasioApp/tests/ | rg -v helpers.py"` returns empty
- [x] 5.4 Run full Django suite: `python manage.py test gimnasioApp`
- [x] 5.5 Run full pytest suite: `pytest gimnasioApp/tests/`
- [x] 5.6 Verify pytest collection: `pytest --collect-only gimnasioApp/tests/` shows 89 items (both runners consistent at 89)
- [x] 5.7 Delete `gimnasioApp/tests.py` (original monolith)
- [x] 5.8 Final verification: `python manage.py test gimnasioApp` + `pytest gimnasioApp/tests/` both pass