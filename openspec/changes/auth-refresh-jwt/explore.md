# Explore — auth-refresh-jwt

**Status**: success
**Date**: 2026-08-20
**Branch**: OscarL
**Scope**: READ-ONLY investigation. No source files modified.

## Executive Summary

The JWT refresh flow is broken because the backend login endpoint (`POST /gym/api/v1/token/`) uses the stock SimpleJWT `TokenObtainPairView` (returns `access`+`refresh` in the JSON body, sets NO cookie), while the frontend refresh contract is cookie-based: `refreshAccessToken()` posts to `/token/refresh/` with **no body** and every axios client that matters (`axios.public.ts` for login/refresh, `axios.private.ts` for protected calls) runs with `withCredentials: true`. The stock `TokenRefreshView` reads the refresh token from the request **body**, so the no-body refresh always fails (400), and after a normal login there is no refresh token anywhere the frontend can reach (the body `refresh` is discarded by `authUser.api.ts:11`). `RegisterViewSet` (`gimnasioApp/views.py:128-136`) already implements the correct cookie pattern — set `refresh_token` HttpOnly cookie with `path=/gym/api/v1/token/refresh/` — and `gimnasio/settings.py:228-234` carries the matching (currently vestigial) `AUTH_COOKIE_*` config, confirming the intended design is cookie-based refresh.

The proposed fix direction is **confirmed and correct**: custom `TokenObtainPairView` that sets the refresh cookie, custom `TokenRefreshView` that reads the refresh from the cookie and rotates it, logout via blacklist + cookie clear, plus tests. The frontend contract needs no API changes — the refresh call stays body-less. Refinements discovered during exploration that the proposal MUST absorb: (1) **SameSite=Lax will break cross-site cookie sending in production** (Vercel frontend → Render backend are different sites) — needs `SameSite=None` + `Secure` in prod, or a same-origin API proxy; (2) `ROTATE_REFRESH_TOKENS` is `False` today — must become `True` for rotation+blacklist semantics; (3) logout cannot blacklist today because the refresh token is HttpOnly and unreachable from JS (`getRefreshTokenFromCookie` always returns null) — a server-side logout endpoint (reads cookie, blacklists, clears) is required; (4) there is a duplicate `axiosPublic` (one with, one without `withCredentials`) causing the public register call to silently drop the Set-Cookie; (5) `AuthProvider.initAuth` has an unreachable "session restore from cookie" branch — reloads in new tabs are always logged out.

## Current State (full auth flow today)

### Backend

- **`gimnasioApp/urls.py:36-38`** — all three auth endpoints use stock SimpleJWT views:
  - `path('gym/api/v1/token/', TokenObtainPairView.as_view(), ...)` — returns `{access, refresh}` in body, sets no cookie.
  - `path('gym/api/v1/token/refresh/', TokenRefreshView.as_view(), ...)` — requires `refresh` in the JSON **body**.
  - `path('gym/api/v1/token/blacklist/', TokenBlacklistView.as_view(), ...)` — expects `{refresh}` in body (AllowAny).
- **`gimnasioApp/views.py:82-138` — `RegisterViewSet` (APIView, AllowAny)** — the ONLY place that sets a refresh cookie today:
  - L119: `refresh = RefreshToken.for_user(user)`
  - L121-125: response body = `{message, user, access}` (no `refresh` in body)
  - L128-136: `response.set_cookie(key='refresh_token', value=str(refresh), max_age=604800 /*7d*/, httponly=True, secure=not settings.DEBUG, samesite='Lax', path='/gym/api/v1/token/refresh/')`.
  - This is the exact pattern login is missing.
- **`gimnasio/settings.py:215-235` — SIMPLE_JWT**:
  - `ACCESS_TOKEN_LIFETIME`: 30 min; `REFRESH_TOKEN_LIFETIME`: 7 days
  - `ROTATE_REFRESH_TOKENS`: **False**; `BLACKLIST_AFTER_ROTATION`: **True** (inert without rotation)
  - `UPDATE_LAST_LOGIN: True`; `ALGORITHM: HS256`; `AUTH_HEADER_TYPES: ('Bearer',)`
  - L228-234 vestigial `AUTH_COOKIE_*` (NOT SimpleJWT settings — custom keys, unused by stock views): `AUTH_COOKIE='refresh_token'`, `AUTH_COOKIE_DOMAIN=None`, `AUTH_COOKIE_SECURE=not DEBUG`, `AUTH_COOKIE_HTTP_ONLY=True`, `AUTH_COOKIE_PATH='/gym/api/v1/token/refresh/'`, `AUTH_COOKIE_SAMESITE='Lax'`.
- **`gimnasio/settings.py:32`** — `DEBUG = 'RENDER' not in os.environ` → on Render, DEBUG=False ⇒ `secure=True` for cookies. Dev: secure=False.
- **`gimnasio/settings.py:57`** — `rest_framework_simplejwt.token_blacklist` is installed.
- **`gimnasioApp/middleware.py:1-25`** — `GimnasioMiddleware` manually decodes Bearer `AccessToken` to set `request.gimnasio` when the user is not yet authenticated (DRF auth runs before middleware for API views). Not affected by the change, but any new token endpoints must remain AllowAny.
- SimpleJWT installed: **5.5.1**.

### Frontend

- **`gimnasioReact/src/utils/authStorage.ts:1-14`** — access token stored in **sessionStorage** (`gym_access_token`), NOT localStorage. Per-tab lifetime; survives reload, lost on tab close/new tab.
- **`authStorage.ts:16-19` — `getRefreshTokenFromCookie()`** — reads `document.cookie` for `refresh_token`. Because the cookie is **HttpOnly**, this ALWAYS returns `null` in practice → dead code.
- **`authStorage.ts:21-23` — `clearRefreshCookie()`** — `document.cookie = 'refresh_token=; Max-Age=0; Path=/gym/api/v1/token/refresh/'` (path-only clear; must match the cookie path the backend uses).
- **`gimnasioReact/src/api/users/authUser.api.ts:7-12`** — `login()` posts credentials to `/token/`, returns **only `data.access`** (`LoginResponse` type in `user.dto.ts:17-19` has only `access`). `data.refresh` from the stock view response is discarded.
- **`gimnasioReact/src/api/axios/refreshToken.api.ts:3-6`** — `refreshAccessToken()` posts `axiosPublic.post('/token/refresh/')` with **no body** → fails against the stock `TokenRefreshView` (400). Returns `data.access`.
- **`gimnasioReact/src/api/axios/axios.public.ts:7-13`** — `axiosPublic` WITH `withCredentials: true` (used by login + refresh). Good — login/refresh responses CAN store Set-Cookie.
- **`gimnasioReact/src/api/axios/axios.private.ts:10-12`** — ALSO exports an `axiosPublic` **WITHOUT** `withCredentials`; imported by `users.api.ts:1` for `registerUser` (L8-11, `POST /register/`). So the public-register flow would NOT store the cookie. Two different `axiosPublic` instances — latent inconsistency.
- **`axios.private.ts:30-34`** — `isTokenExpiringSoon(token, 5*60*1000)`.
- **`axios.private.ts:37-52`** — refresh queue (`isRefreshing`, `failedQueue`, `processQueue`) — concurrent 401 dedupe already implemented.
- **`axios.private.ts:55-81`** — request interceptor: proactive refresh when token has <5 min to expiry, sets `Authorization: Bearer`.
- **`axios.private.ts:84-143`** — response interceptor: on 401 (non-retry) → single refresh, queue others; on refresh failure: `clearAccessToken()`, `clearRefreshCookie()`, `window.location.href = '/login'` (L127-138).
- **`axios.private.ts:148-171`** — `startSilentRefresh(20min)` / `stopSilentRefresh()`.
- **`gimnasioReact/src/layouts/LayoutAdmin.tsx:15-21`** — `useInactivityTimeout(30 min, logout)`; `startSilentRefresh()` on mount, `stopSilentRefresh()` on unmount. Silent refresh only runs inside the admin layout.
- **`gimnasioReact/src/context/AuthProvider.tsx:21-41` — `initAuth`** — reads sessionStorage token + `getRefreshTokenFromCookie()` (always null): L26-29 no token & no refresh → logged out; **L31-35 "no token but refresh cookie → authenticated" is an unreachable branch** (HttpOnly). Session restore from cookie never works.
- **`AuthProvider.tsx:81-96` — `performLogout`** — `getRefreshTokenFromCookie()` returns null → the `POST /token/blacklist/ {refresh}` call is **always skipped**; then `clearAccessToken()` + `clearRefreshCookie()`. So logout NEVER blacklists server-side; an issued refresh token stays valid 7 days. `logout()` (L115-117) doesn't await `performLogout`.
- **`AuthProvider.tsx:98-113` — `login`** — stores access in sessionStorage, sets authenticated, loads user profile.
- **`gimnasioReact/src/pages/auth/LoginPage.tsx:32-48`** — onSubmit → `login()` → navigate `/dashboard`.
- **`gimnasioReact/src/pages/auth/RegisterPage.tsx:23-45`** — uses `CreateUsers` (`POST /User/`, admin flow). `registerUser` (`users.api.ts:8`) is **not used anywhere** — the public `/register/` endpoint is dead code from the frontend's perspective, so the register cookie flow is currently unreachable.
- **`gimnasioReact/src/routes/protectedRoute/ProtectRoute.tsx:12-15`** — `!isAuthenticated` → `<Navigate to="/" />` (→ `/login`).
- **`gimnasioReact/src/pages/Error404.tsx:11`** — vestigial `localStorage.getItem('token')` (key `token` is never written by any code).
- **`gimnasioReact/vercel.json:1-8`** — SPA rewrites only; **no API proxy**.

### CORS / Cookie implications

- Dev: frontend `http://localhost:5173` → backend `http://localhost:8000` — **same-site** (ports don't change the site). SameSite=Lax + `withCredentials` + `CORS_ALLOW_CREDENTIALS=True` works.
- Prod: frontend `https://controlfit.vercel.app` → backend on Render (repo only has the placeholder `https://tu-backend-en-render.com/gym/api/v1` in `gimnasioReact/.env:5`; the real value lives in Vercel env vars) — **cross-site** (different registrable domains). `SameSite=Lax` cookies are **not sent on cross-site XHR/fetch** — the refresh cookie would never reach `POST /token/refresh/`. Fix options: `SameSite=None` + `Secure` in production, or a same-origin proxy (Vercel rewrite of `/gym/api/v1/*` → Render; note `vercel.json` currently only rewrites to `index.html`).
- `settings.py:238` `CORS_ALLOW_CREDENTIALS = True`; L239-243 effective `CORS_ALLOWED_ORIGINS = [http://localhost:5173, http://localhost:3000, https://controlfit.vercel.app]` — django-cors-headers echoes the exact origin, so credentialed requests are covered. `settings.py:194` defines `CORS_ALLOWED_ORIGINS` a second time (without localhost:3000) — the later definition wins; duplicate is vestigial cleanup.
- `AUTH_COOKIE_DOMAIN=None` → host-only cookie scoped to the backend domain — correct for direct-to-Render calls; incompatible with a Vercel-proxy approach unless the proxy preserves the backend host or the cookie domain is changed.

### Existing tests (`gimnasioApp/tests.py`, 1917 lines)

- Coverage: middleware, multi-tenant mixin, UserViewSet create, Supabase storage, avatar serializer/integration, membresias (multiplier/discount/seed), pagos (validation/integration/dashboard), calendario (model/viewsets/range filter/public endpoint), notificaciones (model/manager/viewsets).
- **ZERO auth tests**: no register, login, token obtain, token refresh, blacklist, or cookie assertions. All grep hits for "token/refresh/cookie" in tests.py are `force_authenticate` / `refresh_from_db` (unrelated).
- **Missing (must be added)**: login sets refresh cookie with correct attributes; refresh via cookie returns new access; refresh with invalid/absent cookie → 401; rotation blacklists the old refresh (reuse rejected); logout endpoint blacklists + clears cookie; multi-tab rotation race behavior.

## Affected Areas

### Backend
- `gimnasioApp/views.py` — add cookie-based `TokenObtainPairView` subclass (set cookie on login, mirroring `RegisterViewSet:128-136`); add cookie-based `TokenRefreshView` subclass (read refresh from cookie, rotate, re-set cookie); optionally add a logout view (read cookie → blacklist → clear).
- `gimnasioApp/urls.py:36-38` — swap stock views for the custom ones; keep `/token/blacklist/` (or replace with the logout endpoint).
- `gimnasio/settings.py:215-235` — set `ROTATE_REFRESH_TOKENS: True`; make `AUTH_COOKIE_SAMESITE` conditional (`None` in prod, `Lax` in dev) or adopt same-origin proxying; remove duplicate `CORS_ALLOWED_ORIGINS` (L194 vs L239).
- `gimnasioApp/tests.py` — new auth test classes (see gaps above).

### Frontend (impact of a cookie-based fix)
- `gimnasioReact/src/api/axios/refreshToken.api.ts` — **no change** (already body-less; contract preserved).
- `gimnasioReact/src/api/users/authUser.api.ts` — **no change** (keeps `data.access`; cookie arrives via Set-Cookie since it uses the `withCredentials` axiosPublic).
- `gimnasioReact/src/api/axios/axios.public.ts` — no change; SameSite fix is backend-side.
- `gimnasioReact/src/api/axios/axios.private.ts` — no change required for the core fix; response interceptor already redirects to `/login` on refresh failure.
- `gimnasioReact/src/utils/authStorage.ts` — `getRefreshTokenFromCookie` is dead (HttpOnly); `clearRefreshCookie` path must match backend cookie path. Consider removing/reworking the dead function.
- `gimnasioReact/src/context/AuthProvider.tsx` — `initAuth` unreachable branch (L31-35); logout needs a server-side logout call (or relies on rotation); consider an on-mount refresh attempt to restore sessions across tabs.
- `gimnasioReact/src/api/users/users.api.ts` — `registerUser` uses the wrong `axiosPublic` (no `withCredentials`) — fix if public register is ever wired.
- `gimnasioReact/src/layouts/LayoutAdmin.tsx` — unchanged (silent refresh wiring stays).

## Approaches

1. **Complete the cookie-based flow (recommended)** — custom `TokenObtainPairView` (Set-Cookie refresh), custom `TokenRefreshView` (read cookie, rotate, re-set), logout endpoint (blacklist + clear), `ROTATE_REFRESH_TOKENS=True`, `SameSite=None` in prod, tests.
   - Pros: matches the existing frontend contract exactly (body-less refresh); mirrors the working `RegisterViewSet` pattern; HttpOnly refresh improves XSS posture; reuses installed blacklist app; minimal frontend churn.
   - Cons: cross-site SameSite complexity in prod; rotation requires multi-tab race handling; settings cleanup needed; new backend surface (2-3 views + tests).
   - Effort: Medium.

2. **Switch frontend to body-based refresh** — keep stock views, send `{refresh}` from a non-HttpOnly storage (e.g., localStorage).
   - Pros: minimal backend work (zero).
   - Cons: breaks the entire existing cookie scaffolding (`AUTH_COOKIE_*`, `withCredentials`, register cookie, `clearRefreshCookie`); refresh token in localStorage is XSS-exposed; contradicts the codebase's evident design direction; touches every frontend auth file. Rejected.

3. **Same-origin API proxy on Vercel** — proxy `/gym/api/v1/*` → Render and use relative `VITE_API_URL_PROD`; keep SameSite=Lax.
   - Pros: cookies become same-site; Lax suffices; simpler security posture.
   - Cons: requires `vercel.json` rewrite changes + env change; cookie host-only domain still needs care; adds infrastructure coupling; can't be fully validated locally. Viable as an alternative to `SameSite=None`, not required for the core fix.

### Recommendation

**Approach 1** — complete the cookie-based flow. It is the only option that preserves the frontend contract, matches the pattern already proven in `RegisterViewSet`, and uses the installed blacklist infrastructure. The proposal should also include: `ROTATE_REFRESH_TOKENS=True`, production `SameSite=None` (or proxy, decided explicitly), server-side logout (cookie→blacklist→clear), removal of dead `getRefreshTokenFromCookie`/initAuth branch (or a real on-mount refresh attempt), `users.api.ts` axiosPublic fix, and the CORS duplicate cleanup. Tests must cover the full login→refresh→access path with cookie assertions.

## Risks

- **SameSite cross-site breakage in production** — the single biggest deployment risk; must be resolved explicitly (None+Secure vs proxy) or the fix will work locally and fail on Vercel→Render.
- **Token rotation race across tabs** — with rotation enabled, two tabs refreshing simultaneously can blacklist each other's tokens → spurious logout. Frontend queue is per-tab, not cross-tab.
- **Session restore illusion** — HttpOnly cookie is invisible to JS; `initAuth` cannot detect a valid session on a fresh tab (sessionStorage is per-tab). Users may be logged out on every new tab. Decide whether to attempt on-mount refresh for restore.
- **Logout blacklist currently no-op** — JS cannot read the token; without a server-side logout endpoint, rotated/expired refresh tokens remain valid until their 7-day expiry.
- **Register flow inconsistency** — `registerUser` uses the credential-less `axiosPublic`; if public register gets wired to UI later, the cookie silently won't be stored.
- **Vestigial config confusion** — `AUTH_COOKIE_*` block and duplicate `CORS_ALLOWED_ORIGINS` may mislead future maintainers; clean up as part of the change.
- **Middleware double auth** — `GimnasioMiddleware` manually decodes Bearer tokens; new token endpoints must stay AllowAny and must not accidentally trigger gimnasio lookups.

## Ready for Proposal

Yes — the diagnosis is verified end-to-end with exact file:line evidence, and the recommended approach (cookie-complete flow) is confirmed as the only direction consistent with the existing frontend contract and backend scaffolding. Proposal should fold in the five refinements above (SameSite, rotation, server-side logout, dead-code removal, axiosPublic fix) and the test gaps.