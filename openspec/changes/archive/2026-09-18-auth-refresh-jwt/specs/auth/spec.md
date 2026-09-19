# auth Specification

## Purpose

Cookie-based JWT authentication for staff users: login sets an HttpOnly refresh cookie, refresh rotates it via body-less POST, and logout invalidates server-side. Replaces stock SimpleJWT token views while preserving the existing frontend contract (body-less `refreshAccessToken()` POST to `/token/refresh/`). Covers cookie attribute management, SameSite strategy, rotation, multi-tab edge cases, and auth test requirements.

## Requirements

### Requirement: Cookie-Setting Login

The system SHALL provide a custom login endpoint at `POST /gym/api/v1/token/` that validates credentials via SimpleJWT's `TokenObtainPairSerializer`, sets the refresh token as an HttpOnly cookie, and returns ONLY `{"access": "<token>"}` in the body. The refresh cookie SHALL have attributes: `key=refresh_token`, `path=/gym/api/v1/token/refresh/`, `max_age=604800` (7 days), `httponly=True`, `secure=not settings.DEBUG`, `samesite='None' if not settings.DEBUG else 'Lax'`. The endpoint SHALL NOT return the refresh token in the JSON body under any circumstance.

#### Scenario: Successful login sets refresh cookie and returns access

- GIVEN a valid staff user with username "admin" and password "secret"
- WHEN POST `/gym/api/v1/token/` with `{"username": "admin", "password": "secret"}`
- THEN response status is 200
- AND response body contains `{"access": "<jwt>"}`
- AND response body does NOT contain a `refresh` field
- AND response sets cookie `refresh_token` with `httponly=True`, `path=/gym/api/v1/token/refresh/`, `max_age=604800`
- AND cookie `samesite` is `None` when `settings.DEBUG` is False, or `Lax` when True
- AND cookie `secure` matches `not settings.DEBUG`

#### Scenario: Invalid credentials returns error and sets no cookie

- GIVEN a user with incorrect password
- WHEN POST `/gym/api/v1/token/` with `{"username": "admin", "password": "wrong"}`
- THEN response status is 401
- AND response body contains error detail (e.g. `{"detail": "No active account..."}`)
- AND no `refresh_token` cookie is set on the response

#### Scenario: Missing fields returns 400

- GIVEN no request body
- WHEN POST `/gym/api/v1/token/` with empty body
- THEN response status is 400
- AND response contains validation errors for `username` and `password`

#### Scenario: Login uses AllowAny permission

- GIVEN the `GimnasioMiddleware` is active
- WHEN POST `/gym/api/v1/token/` is called
- THEN the endpoint is accessible without authentication (AllowAny)
- AND GimnasioMiddleware does NOT reject the request due to missing Bearer token

### Requirement: Cookie-Reading Refresh with Rotation

The system SHALL provide a custom refresh endpoint at `POST /gym/api/v1/token/refresh/` that reads the refresh token from the `refresh_token` cookie (NOT from the request body), validates it, generates a rotated refresh token (when `ROTATE_REFRESH_TOKENS=True`), sets the new refresh as an HttpOnly cookie, and returns ONLY `{"access": "<new_token>"}` in the body. The old refresh token SHALL be blacklisted when `BLACKLIST_AFTER_ROTATION=True`. The endpoint SHALL stay AllowAny.

#### Scenario: Successful refresh returns new access and rotates cookie

- GIVEN a valid refresh cookie set by a previous login
- WHEN POST `/gym/api/v1/token/refresh/` with no body (cookie sent automatically)
- THEN response status is 200
- AND response body contains `{"access": "<new_jwt>"}`
- AND response sets a NEW `refresh_token` cookie (rotated token)
- AND the old refresh token is blacklisted in the token blacklist table

#### Scenario: Refresh with no cookie returns 401

- GIVEN no `refresh_token` cookie is present
- WHEN POST `/gym/api/v1/token/refresh/` with no body
- THEN response status is 401
- AND response body contains `{"detail": "No refresh token"}`

#### Scenario: Refresh with expired cookie returns 401

- GIVEN a `refresh_token` cookie containing an expired refresh token
- WHEN POST `/gym/api/v1/token/refresh/` with no body
- THEN response status is 401
- AND response body contains an error detail about invalid/expired token

#### Scenario: Refresh with blacklisted cookie returns 401

- GIVEN a refresh token that was previously used (and thus blacklisted by rotation)
- WHEN POST `/gym/api/v1/token/refresh/` with that cookie
- THEN response status is 401
- AND response body contains an error about the token being blacklisted

#### Scenario: Refresh uses AllowAny permission

- GIVEN the `GimnasioMiddleware` is active
- WHEN POST `/gym/api/v1/token/refresh/` is called
- THEN the endpoint is accessible without authentication (AllowAny)

### Requirement: Multi-Tab Rotation Behavior

The system SHALL use simple refresh token rotation (`ROTATE_REFRESH_TOKENS=True`, `BLACKLIST_AFTER_ROTATION=True`). When two browser tabs both attempt to refresh concurrently, one tab's refresh will succeed and the other will fail (old token blacklisted by the first). The failed tab SHALL receive a 401 response. The system SHALL NOT implement cross-tab synchronization (no BroadcastChannel, no tab coordination). Occasional spurious logouts in a second tab are ACCEPTED behavior.

#### Scenario: Two tabs refresh concurrently — one succeeds, one gets 401

- GIVEN two tabs both have the same refresh cookie (from a shared login)
- WHEN both tabs POST `/gym/api/v1/token/refresh/` at approximately the same time
- THEN one tab receives 200 with a new access token
- AND the other tab receives 401 (its old refresh token was blacklisted by the first)
- AND the 401 tab is expected to redirect to `/login`

#### Scenario: Sequential refresh across tabs works correctly

- GIVEN tab A and tab B share a refresh cookie
- WHEN tab A refreshes successfully (200, new cookie set)
- AND tab B refreshes AFTER tab A's request completes
- THEN tab B's refresh uses the OLD cookie value (which is now blacklisted)
- AND tab B receives 401

### Requirement: Server-Side Logout

The system SHALL provide a logout endpoint at `POST /gym/api/v1/auth/logout/` that reads the refresh token from the `refresh_token` cookie, blacklists it (if present and valid), clears the cookie, and returns 200. The endpoint SHALL be idempotent: logout without a cookie or with an already-blacklisted token SHALL still return 200 (or 204) and clear the cookie. The endpoint SHOULD accept AllowAny (no authentication required to call logout — the cookie itself is the credential).

#### Scenario: Successful logout blacklists token and clears cookie

- GIVEN a valid refresh cookie from a previous login
- WHEN POST `/gym/api/v1/auth/logout/` with the cookie
- THEN response status is 200
- AND the refresh token is blacklisted in the token blacklist table
- AND the `refresh_token` cookie is cleared (Max-Age=0)
- AND a subsequent POST `/gym/api/v1/token/refresh/` with the old cookie returns 401

#### Scenario: Logout without cookie is idempotent

- GIVEN no `refresh_token` cookie is present
- WHEN POST `/gym/api/v1/auth/logout/`
- THEN response status is 200 (or 204)
- AND no error is raised

#### Scenario: Logout with already-blacklisted token is idempotent

- GIVEN a refresh token that was already blacklisted (e.g. by rotation or previous logout)
- WHEN POST `/gym/api/v1/auth/logout/` with that cookie
- THEN response status is 200 (or 204)
- AND the cookie is cleared
- AND no exception is raised

#### Scenario: Logout uses AllowAny permission

- GIVEN the `GimnasioMiddleware` is active
- WHEN POST `/gym/api/v1/auth/logout/` is called
- THEN the endpoint is accessible without authentication

### Requirement: Frontend Login Contract Preservation

The frontend login flow SHALL remain unchanged: `authUser.api.ts` posts credentials to `/token/refresh/`, stores ONLY `data.access` in sessionStorage. The `refreshAccessToken()` function in `refreshToken.api.ts` SHALL remain a body-less POST to `/token/refresh/`. No frontend API shape changes are required for this change.

#### Scenario: Login stores access token only

- GIVEN a successful login response with `{"access": "<jwt>"}`
- WHEN `authUser.api.ts` processes the response
- THEN only `data.access` is stored in sessionStorage (key `gym_access_token`)
- AND `data.refresh` is not referenced or stored

#### Scenario: refreshAccessToken sends no body

- GIVEN the `refreshAccessToken` function
- WHEN it calls POST `/token/refresh/`
- THEN the request body is empty (no `refresh` field)
- AND `withCredentials: true` is set (cookie is sent)

### Requirement: Frontend On-Mount Session Restore

The frontend `AuthProvider` SHALL attempt a cookie-based session restore on mount. When no access token exists in sessionStorage, `initAuth` SHALL call `refreshAccessToken()` (body-less POST, sends cookie). If successful, the access token is stored and the user profile is loaded. If the refresh fails (401 — cookie expired, missing, or blacklisted), the system SHALL set `loading=false` and redirect to `/login` WITHOUT showing an error toast.

#### Scenario: Session restored on new tab via cookie refresh

- GIVEN a user with a valid refresh cookie but no sessionStorage token (new tab)
- WHEN the AuthProvider mounts and calls `initAuth`
- THEN `refreshAccessToken()` is called (body-less POST, sends cookie)
- AND on success, the new access token is stored in sessionStorage
- AND the user profile is loaded
- AND the user sees the dashboard (no redirect to login)

#### Scenario: Expired cookie shows login page

- GIVEN a user with no valid refresh cookie (expired or missing)
- WHEN the AuthProvider mounts and calls `initAuth`
- THEN `refreshAccessToken()` fails with 401
- AND `loading` is set to false
- AND the user is redirected to `/login`
- AND no error toast is displayed

#### Scenario: Existing access token skips refresh attempt

- GIVEN a user with a valid access token in sessionStorage
- WHEN the AuthProvider mounts
- THEN `refreshAccessToken()` is NOT called
- AND the user profile is loaded directly from the existing token

### Requirement: Frontend Server-Side Logout Call

The `performLogout` function in `AuthProvider` SHALL call `POST /gym/api/v1/auth/logout/` (with `withCredentials: true`) before clearing local state. This ensures the server blacklists the refresh token. After the server call (success or failure), the frontend SHALL clear sessionStorage, set `isAuthenticated=false`, set `user=null`, clear the refresh cookie, and navigate to `/login`. The server call failure SHALL be caught and ignored (server may be down — still clear locally).

#### Scenario: Logout calls server endpoint before clearing state

- GIVEN an authenticated user
- WHEN `performLogout` is called
- THEN `POST /gym/api/v1/auth/logout/` is called with `withCredentials: true`
- AND after the call completes, sessionStorage is cleared
- AND `isAuthenticated` becomes false
- AND `user` becomes null
- AND the refresh cookie is cleared client-side
- AND the user is navigated to `/login`

#### Scenario: Logout works even if server call fails

- GIVEN the server is unreachable
- WHEN `performLogout` is called
- THEN the `POST /auth/logout/` call fails
- AND the failure is caught (no error thrown)
- AND sessionStorage is still cleared
- AND `isAuthenticated` becomes false
- AND the user is navigated to `/login`

### Requirement: Duplicate axiosPublic Fix

The `users.api.ts` file SHALL import `axiosPublic` from `axios.public.ts` (which has `withCredentials: true`). The duplicate `axiosPublic` export in `axios.private.ts` (which lacks `withCredentials`) SHALL NOT be used for requests that receive Set-Cookie headers. This ensures the register endpoint's Set-Cookie is not silently dropped. (Register functionality itself is out of scope — this is in-scope hygiene.)

#### Scenario: Register request sends credentials

- GIVEN the `registerUser` function in `users.api.ts`
- WHEN it calls POST `/User/` (or the register endpoint)
- THEN the request includes `withCredentials: true`
- AND any `Set-Cookie` header from the response is honored by the browser

#### Scenario: axiosPublic from axios.private.ts is not used for cookie-receiving requests

- GIVEN the `axiosPublic` export in `axios.private.ts`
- WHEN any API client needs to receive Set-Cookie headers
- THEN it uses `axiosPublic` from `axios.public.ts` instead

### Requirement: Config Cleanup

The system SHALL set `ROTATE_REFRESH_TOKENS=True` in `gimnasio/settings.py` SIMPLE_JWT block. The duplicate `CORS_ALLOWED_ORIGINS` definition at L194 SHALL be removed (keep the definition at L239-243 which includes `localhost:3000`). The vestigial `AUTH_COOKIE_*` block (L228-234) SHALL be wired into the shared `auth_cookie.py` helper or removed if fully superseded by the helper's direct `settings.DEBUG` reads. The shared helper (`auth_cookie.py`) SHALL be the single source of truth for cookie attributes.

#### Scenario: ROTATE_REFRESH_TOKENS is True

- GIVEN the Django settings
- WHEN inspecting `SIMPLE_JWT['ROTATE_REFRESH_TOKENS']`
- THEN the value is `True`

#### Scenario: Single CORS_ALLOWED_ORIGINS definition

- GIVEN the Django settings
- WHEN searching for `CORS_ALLOWED_ORIGINS`
- THEN there is exactly one definition (at L239-243)
- AND the duplicate at L194 is removed

#### Scenario: Shared helper is single source for cookie attributes

- GIVEN the `set_refresh_cookie` function in `gimnasioApp/auth_cookie.py`
- WHEN called from login, refresh, or logout views
- THEN it reads `AUTH_COOKIE_SECURE` and `AUTH_COOKIE_SAMESITE` from settings
- AND all views use the same cookie attributes (no per-view duplication)

### Requirement: Auth Integration Tests

The system SHALL provide integration test classes covering: login sets cookie with exact attributes, refresh from cookie works and rotates, refresh without cookie returns 401, logout blacklists and clears cookie, logout is idempotent without cookie. The existing test suite (`python manage.py test gimnasioApp`) SHALL remain green after adding these tests.

#### Scenario: Login integration test

- GIVEN a staff user in the test database
- WHEN POST `/gym/api/v1/token/` with valid credentials
- THEN `response.cookies['refresh_token']` exists with `httponly=True`, correct `path`, correct `max_age`
- AND `response.data` contains `access` but not `refresh`

#### Scenario: Refresh integration test

- GIVEN a valid refresh token cookie from a previous login
- WHEN POST `/gym/api/v1/token/refresh/` with no body
- THEN `response.status_code` is 200
- AND `response.data` contains a new `access` token
- AND the old refresh token is in the blacklist table
- AND `response.cookies['refresh_token']` is set (rotated)

#### Scenario: Refresh without cookie integration test

- GIVEN no refresh cookie
- WHEN POST `/gym/api/v1/token/refresh/`
- THEN `response.status_code` is 401

#### Scenario: Logout integration test

- GIVEN a valid refresh cookie
- WHEN POST `/gym/api/v1/auth/logout/` with the cookie
- THEN `response.status_code` is 200
- AND the refresh token is blacklisted
- AND `response.cookies['refresh_token']` is cleared

#### Scenario: Logout idempotency integration test

- GIVEN no refresh cookie
- WHEN POST `/gym/api/v1/auth/logout/`
- THEN `response.status_code` is 200 (not 500 or 400)
