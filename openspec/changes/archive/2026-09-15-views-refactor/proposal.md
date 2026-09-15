# Proposal: Refactor views.py into Modular Package

## Intent

Refactor the monolithic `gimnasioApp/views.py` (1,267 lines, 22 classes) into a domain-organized package `gimnasioApp/views/` maintaining full backward compatibility. This addresses technical debt: the single file is too large for effective navigation, code review, and ownership boundaries.

## Scope

### In Scope
- Create `gimnasioApp/views/` package with 10 domain files + `__init__.py`
- Move all 22 ViewSets/classes to appropriate domain files preserving all logic
- `__init__.py` re-exports everything for `from .views import X` compatibility
- Update any internal imports within moved classes
- Run full test suite (91 backend tests) to verify

### Out of Scope
- No API contract changes (endpoints, request/response formats)
- No serializer, model, or service changes
- No test logic changes (only import path updates if needed)
- No URL routing changes

## Capabilities

### New Capabilities
- None (pure refactor)

### Modified Capabilities
- None (no spec-level behavior changes)

## Approach

1. **Create package structure**: `gimnasioApp/views/__init__.py` + 10 domain modules
2. **Move classes by domain** (per exploration analysis):
   - `auth_views.py` (6): CookieTokenObtainPairView, CookieTokenRefreshView, CookieTokenVerifyView, LogoutView, RegisterViewSet, PasswordChangeView
   - `member_views.py` (3): UserViewSet, UsuarioGymViewSet, UsuarioGymDayViewSet
   - `membership_views.py` (2): MembresiaViewSet, MembresiaAsignadaViewSet
   - `payment_views.py` (1): PagoMembresiaViewSet
   - `dashboard_views.py` (4): DashboardStatsView, Home, ActivitiesView, ExportReportView
   - `notification_views.py` (1): NotificationViewSet
   - `calendar_views.py` (3): TipoEventoViewSet, EventoCalendarioViewSet, PublicCalendarioView
   - `platform_views.py` (2): PlatformStatsView, GimnasioPlatformViewSet
   - `utils.py`: validate_csrf, PlatformPagination
   - `profile_views.py`: userProfileView
3. **Backward compatibility**: `__init__.py` imports and re-exports all public classes
4. **Verify**: Run `python manage.py test gimnasioApp` — all 91 tests must pass

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `gimnasioApp/views.py` | Removed | Replaced by package |
| `gimnasioApp/views/__init__.py` | New | Re-exports all classes |
| `gimnasioApp/views/auth_views.py` | New | 6 auth classes (~200 lines) |
| `gimnasioApp/views/member_views.py` | New | 3 member classes (~150 lines) |
| `gimnasioApp/views/membership_views.py` | New | 2 membership classes (~80 lines) |
| `gimnasioApp/views/payment_views.py` | New | 1 payment class (~50 lines) |
| `gimnasioApp/views/dashboard_views.py` | New | 4 dashboard classes (~300 lines) |
| `gimnasioApp/views/notification_views.py` | New | 1 notification class (~50 lines) |
| `gimnasioApp/views/calendar_views.py` | New | 3 calendar classes (~80 lines) |
| `gimnasioApp/views/platform_views.py` | New | 2 platform classes (~150 lines) |
| `gimnasioApp/views/utils.py` | New | validate_csrf, PlatformPagination |
| `gimnasioApp/views/profile_views.py` | New | userProfileView (~30 lines) |
| `gimnasioApp/urls.py` | Unchanged | Imports from `.views` still work |
| `gimnasioApp/tests.py` | Potentially Modified | Import paths may need updates |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Import cycles (views ↔ serializers ↔ models ↔ services) | High | Move imports inside methods where needed; use string imports for type hints; verify no circular deps in test run |
| Test import paths break | Medium | Update test imports if they reference moved classes directly; run tests incrementally per domain |
| MultiTenantViewSetMixin used by all ViewSets | Low | Mixin stays in `mixins.py`; imported from parent module |
| CSRF validation helper used by middleware | Low | Keep `validate_csrf` in `utils.py`; middleware imports from `views.utils` |

## Rollback Plan

1. Delete `gimnasioApp/views/` directory
2. Restore original `gimnasioApp/views.py` from git
3. Run tests to confirm baseline

## Dependencies

- Existing `gimnasioApp/mixins.py` (MultiTenantViewSetMixin)
- Existing `gimnasioApp/serializers.py`, `models.py`, `services/`
- Django test runner: `python manage.py test gimnasioApp`

## Success Criteria

- [ ] All 91 backend tests pass (`python manage.py test gimnasioApp`)
- [ ] `gimnasioApp/urls.py` imports work unchanged (`from .views import ...`)
- [ ] No runtime import errors
- [ ] No API behavior changes
- [ ] Package structure matches domain grouping exactly