# Tasks: JWT Refresh Hardening

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 140 lines (range: 120-160) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | single-pr |
| Chain strategy | size-exception |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Config + CSRF helpers + middleware | PR 1 | `python manage.py test gimnasioApp` | Django test suite | settings.py + auth_cookie.py + views.py |
| 2 | Verify endpoint + frontend integration | PR 2 | `python manage.py test gimnasioApp` + frontend build | Django test suite + npm build | views.py + urls.py + frontend files |
| 3 | Enforcement + cleanup | PR 3 | `python manage.py test gimnasioApp` | Django test suite | settings.py + frontend files |

## Phase 1: Config (lifetimes)

- [x] 1.1 Update `gimnasio/settings.py` SIMPLE_JWT: change ACCESS_TOKEN_LIFETIME from 30min to 15min, REFRESH_TOKEN_LIFETIME from 7days to 3days
- [x] 1.2 Add `CSRF_ENFORCE = False` feature flag to `gimnasio/settings.py` (after SIMPLE_JWT)
- [x] 1.3 Test: verify new lifetimes in config with `python manage.py test gimnasioApp.tests.test_settings`

## Phase 2: CSRF Cookie Helpers + Middleware

- [x] 2.1 Add CSRF cookie helpers to `gimnasioApp/auth_cookie.py`: `set_csrf_cookie()`, `clear_csrf_cookie()`, `get_csrf_token()` with proper attributes (HttpOnly=false, SameSite, Path, Max-Age)
- [x] 2.2 Create `validate_csrf(request)` function in `gimnasioApp/views.py` with log-only mode when CSRF_ENFORCE=False
- [x] 2.3 Update `CookieTokenObtainPairView` (login) to set CSRF cookie on response
- [x] 2.4 Update `CookieTokenRefreshView` (refresh) to set CSRF cookie on response
- [x] 2.5 Update `LogoutView` to clear CSRF cookie on response
- [x] 2.6 Test: cookie set/clear/read with `python manage.py test gimnasioApp.tests.test_csrf_cookie`
- [x] 2.7 Test: middleware log-only mode with `python manage.py test gimnasioApp.tests.test_csrf_validation`

## Phase 3: Verify Endpoint

- [x] 3.1 Create `CookieTokenVerifyView` in `gimnasioApp/views.py`: POST endpoint, permission AllowAny, returns `{valid: true, exp: timestamp}` or 401
- [x] 3.2 Add `/token/verify/` endpoint to `gimnasioApp/urls.py`
- [x] 3.3 Test: verify valid token returns 200 with `python manage.py test gimnasioApp.tests.test_token_verify`
- [x] 3.4 Test: verify expired token returns 401 with `python manage.py test gimnasioApp.tests.test_token_verify`
- [x] 3.5 Test: verify missing token returns 401 with `python manage.py test gimnasioApp.tests.test_token_verify`

## Phase 4: Frontend Integration

- [x] 4.1 Add `verifyToken()` function to `gimnasioReact/src/api/axios/refreshToken.api.ts`: GET `/token/verify/`, returns `{valid: boolean, exp?: number}`
- [x] 4.2 Add CSRF header interceptor to `gimnasioReact/src/api/axios/axios.private.ts`: read `csrftoken` cookie, add `X-CSRF-Token` header for POST/PUT/PATCH/DELETE
- [x] 4.3 Add cookie reader utility `getCsrfCookie(name)` to frontend utils
- [x] 4.4 Add verify call on app mount in auth context (e.g., `AuthProvider.tsx`)
- [x] 4.5 Test: interceptor adds header with `npm test -- --testNamePattern="CSRF interceptor"`
- [x] 4.6 Test: verify call on mount with `npm test -- --testNamePattern="silent validation"`

## Phase 5: Enforcement + Cleanup

- [x] 5.1 Enable `CSRF_ENFORCE=True` in `gimnasio/settings.py`
- [x] 5.2 Remove `startSilentRefresh`/`stopSilentRefresh` from `axios.private.ts`
- [x] 5.3 Update auth context to use verify-based validation instead of interval refresh (already done in Phase 4)
- [x] 5.4 Test: CSRF missing returns 403 with `python manage.py test gimnasioApp.tests.CSRFEnforcementIntegrationTest.test_csrf_missing_header_returns_403`
- [x] 5.5 Test: CSRF invalid returns 403 with `python manage.py test gimnasioApp.tests.CSRFEnforcementIntegrationTest.test_csrf_invalid_header_returns_403`
- [x] 5.6 Integration test: full login → mutate → refresh flow with `python manage.py test gimnasioApp.tests.FullAuthFlowIntegrationTest.test_full_login_mutate_refresh_flow`

## Relevant Files

- `gimnasio/settings.py` — JWT lifetimes + CSRF_ENFORCE flag
- `gimnasioApp/auth_cookie.py` — CSRF cookie helpers
- `gimnasioApp/views.py` — CookieTokenVerifyView, validate_csrf
- `gimnasioApp/urls.py` — /token/verify/ endpoint
- `gimnasioReact/src/api/axios/axios.private.ts` — CSRF interceptor
- `gimnasioReact/src/api/axios/refreshToken.api.ts` — verifyToken function
- `gimnasioReact/src/contexts/AuthContext.tsx` — verify on mount
