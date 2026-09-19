# Tasks: auth-refresh-jwt

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~297 (backend ~260, frontend ~37) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-always |
| Chain strategy | pending |

Decision needed before apply: Yes
Chained PRs recommended: No
Chain strategy: pending
400-line budget risk: Low

### Suggested Work Units

| Unit | Goal | Likely PR | Focused test command | Runtime harness | Rollback boundary |
|------|------|-----------|----------------------|-----------------|-------------------|
| 1 | Shared cookie helper + custom views + settings | PR 1 | `python manage.py test gimnasioApp` | Manual login/refresh/logout in browser | auth_cookie.py, views.py, urls.py, settings.py |
| 2 | Frontend wiring + integration tests | PR 1 | `npm run build` | New tab session restore, logout flow | AuthProvider.tsx, users.api.ts, authStorage.ts, tests.py |

## Phase 1: Foundation — Shared Cookie Helper

- [x] 1.1 Create `gimnasioApp/auth_cookie.py` with `set_refresh_cookie(response, refresh_token)` and `clear_refresh_cookie(response)` helpers. Read `AUTH_COOKIE_SECURE` and `AUTH_COOKIE_SAMESITE` from settings. Cookie attrs: key=`refresh_token`, max_age=604800, httponly=True, secure=not DEBUG, samesite='None' if not DEBUG else 'Lax', path='/gym/api/v1/token/refresh/'.
- [x] 1.2 Update `RegisterViewSet` (views.py:128-136) to use `set_refresh_cookie()` from shared helper instead of inline `response.set_cookie()`.

## Phase 2: Backend — Custom JWT Views

- [x] 2.1 Add `CookieTokenObtainPairView` to `gimnasioApp/views.py`: subclass `TokenObtainPairView`, override `post()` to call `super().post()`, extract refresh from response body, call `set_refresh_cookie()`, delete refresh from body, return only `{access}`. Permission: `AllowAny`.
- [x] 2.2 Add `CookieTokenRefreshView` to `gimnasioApp/views.py`: subclass `TokenRefreshView`, override `post()` to read `request.COOKIES.get('refresh_token')`, return 401 if missing, inject into `request.data['refresh']`, call `super().post()`, on success extract new refresh from response, call `set_refresh_cookie()`, delete refresh from body, return only `{access}`. Permission: `AllowAny`.
- [x] 2.3 Add `LogoutView` to `gimnasioApp/views.py`: APIView with `AllowAny`, read `request.COOKIES.get('refresh_token')`, blacklist via `RefreshToken(token).blacklist()` in try/except, call `clear_refresh_cookie()`, return `{'detail': 'Logged out'}`. Permission: `AllowAny`.
- [x] 2.4 Update `gimnasioApp/urls.py`: import custom views, swap `TokenObtainPairView` (L36) → `CookieTokenObtainPairView`, swap `TokenRefreshView` (L37) → `CookieTokenRefreshView`, add `path('gym/api/v1/auth/logout/', LogoutView.as_view(), name='auth_logout')`. Remove `TokenBlacklistView` import and path.

## Phase 3: Settings Cleanup

- [x] 3.1 Set `ROTATE_REFRESH_TOKENS=True` in `gimnasio/settings.py` SIMPLE_JWT block (L218).
- [x] 3.2 Remove duplicate `CORS_ALLOWED_ORIGINS` at L194 (keep L239-243).
- [x] 3.3 Update `AUTH_COOKIE_SAMESITE` (L234) to `'None' if not DEBUG else 'Lax'` or remove vestigial block entirely (helper reads `settings.DEBUG` directly).

## Phase 4: Frontend Wiring

- [x] 4.1 Fix `gimnasioReact/src/api/users/users.api.ts` L1: change import from `{ axiosPrivate, axiosPublic } from "../axios/axios.private"` to `{ axiosPublic } from "../axios/axios.public"` + `{ axiosPrivate } from "../axios/axios.private"`. Register flow now sends `withCredentials: true`.
- [x] 4.2 Update `AuthProvider.tsx` `initAuth` (L22-41): remove `getRefreshTokenFromCookie()` call. If no access token in sessionStorage, attempt `refreshAccessToken()` (body-less POST, sends cookie). On success → store access + load profile. On failure → `setLoading(false)`, no toast.
- [x] 4.3 Update `AuthProvider.tsx` `performLogout` (L81-96): replace blacklist call with `POST /auth/logout/` (body-less, `withCredentials: true`). Keep local cleanup: `clearAccessToken()`, `clearRefreshCookie()`, `setUser(null)`, `setIsAuthenticated(false)`. Remove `getRefreshTokenFromCookie` import.
- [x] 4.4 Remove dead `getRefreshTokenFromCookie` from `authStorage.ts` (L16-19). Keep `clearRefreshCookie` (L21-23).

## Phase 5: Auth Integration Tests

- [x] 5.1 Add `AuthCookieLoginTest` class to `gimnasioApp/tests.py`: test login sets `refresh_token` cookie with correct attrs (httponly, path, max_age, samesite, secure); test login returns `{access}` only (no refresh in body); test invalid credentials returns 401 and no cookie.
- [x] 5.2 Add `AuthCookieRefreshTest` class to `gimnasioApp/tests.py`: test refresh from cookie returns new access + rotates (old blacklisted); test refresh with no cookie returns 401; test refresh with expired cookie returns 401.
- [x] 5.3 Add `AuthCookieLogoutTest` class to `gimnasioApp/tests.py`: test logout blacklists token + clears cookie; test subsequent refresh with old cookie returns 401; test logout without cookie is idempotent (200).
- [x] 5.4 Run full regression: `python manage.py test gimnasioApp` — all existing + new tests green.

## Phase 6: Manual Verification

- [ ] 6.1 Manual test: login via browser → verify refresh_token cookie set with correct attrs in DevTools → verify session survives > 30 min via silent refresh.
- [ ] 6.2 Manual test: new tab → verify on-mount session restore (no re-login needed if cookie valid).
- [ ] 6.3 Manual test: logout → verify cookie cleared + subsequent refresh returns 401.
- [ ] 6.4 Cross-site test (prod): after deploy, verify on controlfit.vercel.app that cookie has SameSite=None, Secure, correct Path.

## Relevant Files

| File | Action | Phase |
|------|--------|-------|
| `gimnasioApp/auth_cookie.py` | Create | 1 |
| `gimnasioApp/views.py` | Modify (+3 views, update RegisterViewSet) | 1-2 |
| `gimnasioApp/urls.py` | Modify (swap views, add logout) | 2 |
| `gimnasio/settings.py` | Modify (ROTATE, CORS, SameSite) | 3 |
| `gimnasioReact/src/api/users/users.api.ts` | Modify (fix import) | 4 |
| `gimnasioReact/src/context/AuthProvider.tsx` | Modify (initAuth, performLogout) | 4 |
| `gimnasioReact/src/utils/authStorage.ts` | Modify (remove dead function) | 4 |
| `gimnasioApp/tests.py` | Modify (+3 test classes) | 5 |
