# Apply Progress: auto-crear-gym-desde-demo

**Change**: auto-crear-gym-desde-demo
**Batch**: 1 (complete implementation) — 23/23 tasks complete
**Date**: 2026-08-26
**Mode**: Strict TDD (pytest + vitest) — all phases followed RED→GREEN→REFACTOR
**Delivery**: 3 chained PRs (feature-branch-chain: PR 1→tracker, PR 2→PR 1, PR 3→PR 2)
**Review budget**: 400 lines per PR

---

## Phase Summary

### Phase 1: Foundation (Models + Migration) ✅
**Files**: `gimnasioApp/models.py`, migration `0012_auto_20260826_0330.py`, `gimnasioApp/serializers.py`
**Tests**: 3 TDD tests (163 total passing)
- Added `DemoRequest.gym_creado` FK (nullable, SET_NULL, related_name=demo_origen)
- Added `Usuario.must_change_password` BooleanField(default=False)
- Migration `0012` created and applied (additive, zero-downtime)
- DemoRequestSerializer includes `gym_creado` nested (read_only)

### Phase 2: Backend Core (Service Layer + ViewSet) ✅
**Files**: `gimnasioApp/services/onboarding.py`, `gimnasioApp/views.py`, `gimnasioApp/serializers.py`
**Tests**: 12 TDD tests (163 total passing)
- `generate_temp_password()`: 12-char URL-safe via `secrets.token_urlsafe(12)`
- `provision_gym_from_demo(demo)`: atomic create Gimnasio + admin Usuario + link demo; raises ValidationError on duplicate email
- `revert_gym_from_demo(demo)`: soft-delete gym.is_active=False, admin.is_active=False, demo.gym_creado=None
- DemoRequestViewSet.perform_update: idempotent pendiente→contactado, reverse contactado→pendiente with cleanup
- email_sent SerializerMethodField returns True when gym_creado exists

### Phase 3: Email Service + Templates ✅
**Files**: `gimnasioApp/services/email.py`, `templates/emails/welcome_admin.html`, `templates/emails/welcome_admin.txt`, `gimnasio/settings.py`
**Tests**: 8 TDD tests (163 total passing)
- `send_welcome_email(gym_id, admin_id, temp_password)`: sync send_mail, fire-and-forget with logging, never raises
- HTML + plain text templates with ControlFit branding, admin email, temp password, login link, must-change notice
- EMAIL config via env vars: console backend (dev), SMTP (prod), FRONTEND_URL, SUPPORT_EMAIL
- transaction.on_commit wiring in perform_update; failure logs + email_sent=False without rollback

### Phase 4: Password Change Flow ✅
**Files**: `gimnasioApp/views.py` (PasswordChangeView), `gimnasioApp/permissions.py` (RequirePasswordChange), `gimnasioReact/src/pages/auth/PasswordChangeRequiredPage.tsx`, `gimnasioReact/src/context/AuthProvider.tsx`, `gimnasioReact/src/api/axios/axios.private.ts`, `gimnasioReact/src/routes/protectedRoute/ProtectRoute.tsx`, `gimnasioReact/src/model/dto/user.dto.ts`
**Tests**: 14 backend + 10 frontend TDD tests (163 + 38 passing)
- POST /auth/password/change/ endpoint with validation
- RequirePasswordChange permission checks must_change_password flag
- Frontend PasswordChangeRequiredPage with form validation, show/hide password
- AuthProvider loads must_change_password from /me/ profile
- ProtectedRoute redirects to /cambiar-password/ when flag is true
- On success: removes gym_access_token, navigates to /login

### Phase 5: Frontend Integration ✅
**Files**: `gimnasioReact/src/api/action/demoRequests.api.ts`, `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.tsx`, `gimnasioReact/src/pages/admin/demo/DemoRequestsPage.test.tsx`
**Tests**: 9 RTL tests (47 total passing)
- DemoRequest type includes gym_creado?
- Smart toasts: "Gimnasio creado" with email, "Revertido a pendiente", generic estado, email duplicate 400
- Loading spinner on badge during PATCH; double-click prevention
- No navigation on success (stays on page)

### Phase 6: Verification & Polish ✅
- Lint: eslint clean (2 pre-existing warnings only), no ruff/mypy configured
- TypeScript: tsc passes (test files excluded from build)
- Full test suite: 163 backend + 47 frontend = 210 tests passing

---

## Commits (Work Units)

| Commit | Scope | Files | Test Command |
|--------|-------|-------|--------------|
| `git commit -m "feat: auto-crear-gym-desde-demo - Phase 1: models, migration, serializer"` | PR 1 (backend core) | gimnasioApp/models.py, migrations/0012*, serializers.py | `python manage.py test gimnasioApp` |
| `git commit -m "feat: auto-crear-gym-desde-demo - Phase 2: onboarding service + viewset + integration tests"` | PR 1 (backend core) | gimnasioApp/services/onboarding.py, views.py, tests.py | `python manage.py test gimnasioApp` |
| `git commit -m "feat: auto-crear-gym-desde-demo - Phase 3: email service + templates + config"` | PR 2 (email + templates) | gimnasioApp/services/email.py, templates/emails/*, settings.py, tests.py | `python manage.py test gimnasioApp` |
| `git commit -m "feat: auto-crear-gym-desde-demo - Phase 4: password change backend + frontend"` | PR 3 (frontend) | gimnasioApp/views.py, permissions.py, gimnasioReact/src/pages/auth/, context/, routes/, model/dto/ | `python manage.py test gimnasioApp && npm run test` |
| `git commit -m "feat: auto-crear-gym-desde-demo - Phase 5: DemoRequestsPage smart toast + loading + tests"` | PR 3 (frontend) | gimnasioReact/src/api/action/demoRequests.api.ts, pages/admin/demo/DemoRequestsPage.tsx, tests | `npm run test && npm run build` |
| `git commit -m "chore: auto-crear-gym-desde-demo - lint fixes + TypeScript fixes"` | PR 3 (frontend) | gimnasioReact/src/pages/admin/demo/*.tsx, pages/auth/*.tsx, test/*.tsx | `npm run lint && npm run build` |

---

## Verification Commands

```bash
# Backend
python manage.py test gimnasioApp --keepdb
# 163 tests OK

# Frontend
cd gimnasioReact
npm run lint      # 0 errors, 2 pre-existing warnings
npm run build     # tsc + vite build OK
npm run test      # 47 tests OK
```

---

## Next Steps

1. Create 3 chained PRs on branch `OscarL` (feature-branch-chain strategy)
2. Run `sdd-verify` to validate implementation against specs
3. Run `sdd-archive` to close the change