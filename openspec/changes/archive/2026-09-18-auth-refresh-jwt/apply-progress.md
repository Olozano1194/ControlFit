# Apply Progress: auth-refresh-jwt

## Status
**COMPLETE — implementation + automated verification done.** Phase 6 (manual browser verification) pending human.

## What Was Implemented

### Backend (GREEN — TDD)
- **`gimnasioApp/auth_cookie.py`** (new): `set_refresh_cookie()` / `clear_refresh_cookie()` — single source of truth for cookie attributes. Reads `settings.DEBUG` **dynamically at call time** (dev: SameSite=Lax, no Secure; prod: SameSite=None + Secure). Key `refresh_token`, max_age 604800, httponly, path `/gym/api/v1/token/refresh/`.
- **`gimnasioApp/views.py`**:
  - `CookieTokenObtainPairView` — login sets cookie, strips refresh from body, returns `{access}` only.
  - `CookieTokenRefreshView` — reads refresh from cookie, 401 `{'detail': 'No refresh token'}` if missing, rotates + re-sets cookie, returns `{access}` only.
  - `LogoutView` — blacklists refresh (try/except idempotent), clears cookie, returns `{'detail': 'Logged out'}`.
  - `RegisterViewSet` refactored to use the shared helper.
- **`gimnasioApp/urls.py`**: swapped stock token views for cookie views, removed `/token/blacklist/`, added `gym/api/v1/auth/logout/`.
- **`gimnasio/settings.py`**: `ROTATE_REFRESH_TOKENS=True`, removed vestigial `AUTH_COOKIE_*` block, removed duplicate `CORS_ALLOWED_ORIGINS` (L194).

### Frontend (verified via `npm run build` — tsc + vite pass)
- **`users.api.ts`**: `axiosPublic` now imported from `axios.public.ts` (has `withCredentials: true`) so register receives the refresh cookie.
- **`AuthProvider.tsx`**: `initAuth` restores session via cookie refresh when no access token (silent failure → `setLoading(false)`, ProtectRoute redirects); `performLogout` calls `POST /auth/logout/` (server blacklists + clears cookie), keeps local cleanup.
- **`authStorage.ts`**: removed dead `getRefreshTokenFromCookie`; kept `clearRefreshCookie`.

## Test Results
| Run | Result |
|-----|--------|
| Baseline (pre-change) | 103 tests OK |
| RED (18 new tests, no impl) | FAILED (failures=4, errors=11) — expected |
| Focused auth tests (after impl) | 18/18 OK |
| Full regression | **121/121 OK** (103 + 18) |
| `manage.py check` | No issues |
| `npm run build` (gimnasioReact) | ✓ built (tsc + vite) |

New test classes in `gimnasioApp/tests.py`: `AuthCookieHelperTest` (3), `AuthCookieLoginTest` (4), `AuthCookieRefreshTest` (5), `AuthCookieLogoutTest` (3), `AuthSettingsTest` (3).

## Deviations From Tasks
1. **Task 2.2 "inject into `request.data['refresh']`"**: DRF parses a body-less request into an **immutable QueryDict** (`AttributeError` on assignment). Implemented instead by passing `{'refresh': refresh_token}` directly to `self.get_serializer(data=...)` — identical flow to `TokenViewBase.post` (same TokenError→InvalidToken handling). Same contract, no internal API mutation.
2. **Task 3.3**: chose the "remove vestigial block" option. The helper reads `settings.DEBUG` directly because the Django test runner forces `DEBUG=False` while SIMPLE_JWT values freeze at import — static settings couldn't reflect runtime DEBUG. Spec scenario wording kept (cookie attrs still conditional), implementation approach differs. Authorized by orchestrator.
3. **Task 5.x**: added 2 extra test classes beyond the 3 planned (`AuthCookieHelperTest` for the helper contract, `AuthSettingsTest` for the settings cleanup) — matches the design's test matrix.

## Gotchas Discovered
- `HttpResponseBase.delete_cookie()` in Django 5.2 does **not** accept `secure` (signature: `(key, path='/', domain=None, samesite=None)`) — passing `secure` raises TypeError.
- Django test runner forces `settings.DEBUG=False` via `setup_test_environment()`; any static setting computed from `DEBUG` at import time is frozen/wrong in tests.
- Test-client refresh requests without a body are parsed by FormParser → immutable QueryDict; `request.data['x'] = y` raises `AttributeError`.

## Phase 6 — Manual Verification (PENDING, human)
- [ ] 6.1 Browser login → DevTools: cookie `refresh_token` attrs (HttpOnly, Path=/gym/api/v1/token/refresh/, Max-Age 604800; dev: SameSite=Lax no Secure).
- [ ] 6.2 New tab → session restored on mount (no re-login if cookie valid).
- [ ] 6.3 Logout → cookie cleared + subsequent refresh returns 401.
- [ ] 6.4 After deploy: verify on controlfit.vercel.app cookie is SameSite=None + Secure.

## Environment Issue (pre-existing, NOT caused by this change)
`gimnasioReact/node_modules` was already corrupted (only 3 empty entries; `npm install` failed with errno -4094). Renamed to `node_modules_corrupt_old` (cannot be deleted: "directorio dañado o ilegible" — orphaned NTFS entries). Fresh `npm install` (383 packages) + build work fine. **Recommendation: run `chkdsk F: /f` (admin) when convenient, then delete the parked folder.** Git shows harmless warnings when walking it.

## Commit Plan (proposed — NOT executed, awaiting user approval)
Per tasks artifact, 2 work units, single PR:
1. **Backend**: `auth_cookie.py`, `views.py`, `urls.py`, `settings.py`, `tests.py` → `feat(auth): cookie-based JWT refresh rotation with server-side logout`
2. **Frontend**: `users.api.ts`, `AuthProvider.tsx`, `authStorage.ts` → `feat(auth): wire cookie refresh session restore and logout`

## Risks / Notes
- Multi-tab rotation race: loser gets 401 → interceptor clears session → redirect `/login` (accepted, documented in design).
- `npm install` re-ran (node_modules rebuilt) — `package-lock.json` unchanged? Verify no unintended lockfile diff before committing.
- `.gitignore`/`gimnasioReact/.gitignore` have pre-existing working-tree edits — left untouched.