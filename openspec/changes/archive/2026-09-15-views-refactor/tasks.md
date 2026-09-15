# Tasks: Refactor views.py → Package views/

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~1,300 (11 new files + 1 deletion) |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1: foundation + auth + profile + member → PR 2: membership + payment + notification + calendar → PR 3: dashboard + platform + init + cleanup |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Foundation + core auth/member | PR 1 | `python manage.py test gimnasioApp` | Django test runner | Remove `gimnasioApp/views/` dir, restore `views.py` |
| 2 | Business domains | PR 2 | `python manage.py test gimnasioApp` | Django test runner | Remove 4 new module files |
| 3 | Heavy modules + integration | PR 3 | `python manage.py test gimnasioApp` | Django test runner | Remove last 2 modules + `__init__.py`, restore `views.py` |

---

## Phase 1: Package Foundation

- [ ] 1.1 Create `gimnasioApp/views/` directory + empty `__init__.py`
- [ ] 1.2 Create `gimnasioApp/views/utils.py` — move `validate_csrf` (lines 43-82) and `PlatformPagination` (lines 89-93) with imports from design.md `utils.py` import map

## Phase 2: Auth + Profile + Member (Core Identity)

- [ ] 2.1 Create `gimnasioApp/views/auth_views.py` — move 6 auth classes (lines 147-351) with imports from design.md `auth_views.py` import map
- [ ] 2.2 Create `gimnasioApp/views/profile_views.py` — move `userProfileView` (lines 354-375) with imports from design.md `profile_views.py` import map
- [ ] 2.3 Create `gimnasioApp/views/member_views.py` — move 3 member classes (lines 100-405) with imports from design.md `member_views.py` import map
- [ ] 2.4 Verify: `python -m py_compile gimnasioApp/views/auth_views.py profile_views.py member_views.py utils.py`

## Phase 3: Business Domains

- [ ] 3.1 Create `gimnasioApp/views/membership_views.py` — move 2 classes (lines 593-616) with imports from design.md `membership_views.py` import map
- [ ] 3.2 Create `gimnasioApp/views/payment_views.py` — move 1 class (lines 623-651) with imports from design.md `payment_views.py` import map
- [ ] 3.3 Create `gimnasioApp/views/notification_views.py` — move 1 class (lines 658-702) with imports from design.md `notification_views.py` import map
- [ ] 3.4 Create `gimnasioApp/views/calendar_views.py` — move 3 classes (lines 977-1010) with imports from design.md `calendar_views.py` import map
- [ ] 3.5 Verify: `python -m py_compile gimnasioApp/views/membership_views.py payment_views.py notification_views.py calendar_views.py`

## Phase 4: Heavy Modules + Integration

- [ ] 4.1 Create `gimnasioApp/views/dashboard_views.py` — move 4 classes (lines 412-970) with imports from design.md `dashboard_views.py` import map
- [ ] 4.2 Create `gimnasioApp/views/platform_views.py` — move 3 classes incl. DemoRequestViewSet (lines 1026-1267) with imports from design.md `platform_views.py` import map
- [ ] 4.3 Populate `gimnasioApp/views/__init__.py` — explicit named imports from all 10 submodules + `__all__` list (design.md lines 247-298)
- [ ] 4.4 Verify: `python -m py_compile gimnasioApp/views/__init__.py dashboard_views.py platform_views.py`

## Phase 5: Verification + Cleanup

- [ ] 5.1 Import smoke test: `python -c "from gimnasioApp.views import UserViewSet, CookieTokenObtainPairView, validate_csrf, PlatformPagination"` (all 22 classes + 2 utils)
- [ ] 5.2 Run full test suite: `python manage.py test gimnasioApp --verbosity=1` — confirm 91 tests pass
- [ ] 5.3 Delete original `gimnasioApp/views.py`
- [ ] 5.4 Final test suite run: `python manage.py test gimnasioApp --verbosity=1` — confirm 91 tests still pass
