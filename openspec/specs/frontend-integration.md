# Frontend Integration Specification

## Purpose

Integrate the backend CSRF protection and token verification into the React frontend. The axios interceptor handles CSRF header injection, and the app performs silent session validation on mount.

## Requirements

### Requirement: CSRF Token Injection in Axios Interceptor

The `axiosPrivate` instance SHALL read the `csrftoken` cookie and attach it as the `X-CSRF-Token` header on all mutating requests (POST, PUT, PATCH, DELETE). GET requests SHALL NOT include the header.

#### Scenario: POST request includes CSRF header

- GIVEN a `csrftoken` cookie with value `abc123`
- WHEN `axiosPrivate` sends a POST request
- THEN the request includes header `X-CSRF-Token: abc123`

#### Scenario: GET request omits CSRF header

- GIVEN a `csrftoken` cookie with value `abc123`
- WHEN `axiosPrivate` sends a GET request
- THEN the request does NOT include `X-CSRF-Token` header

#### Scenario: PUT/PATCH/DELETE include CSRF header

- GIVEN a `csrftoken` cookie with value `abc123`
- WHEN `axiosPrivate` sends a PUT, PATCH, or DELETE request
- THEN the request includes header `X-CSRF-Token: abc123`

#### Scenario: Missing CSRF cookie sends empty header

- GIVEN no `csrftoken` cookie is present
- WHEN `axiosPrivate` sends a POST request
- THEN the request includes `X-CSRF-Token` with value `""` or omits the header

### Requirement: Cookie Reader Utility

The system SHALL provide a utility function to read the `csrftoken` cookie value by name. The utility SHALL handle URL-decoded values.

#### Scenario: Read existing CSRF cookie

- GIVEN document.cookie contains `csrftoken=abc%2F123`
- WHEN calling the cookie reader for `csrftoken`
- THEN the returned value is `abc/123` (URL-decoded)

#### Scenario: Read missing cookie returns null

- GIVEN document.cookie does not contain `csrftoken`
- WHEN calling the cookie reader for `csrftoken`
- THEN the returned value is `null`

### Requirement: Silent Session Validation on App Mount

The frontend SHALL call `GET /gym/api/v1/token/verify/` on application mount to validate the current session silently. If the token is invalid, the user SHALL be redirected to login.

#### Scenario: Valid session on mount

- GIVEN a valid access token in memory
- WHEN the app mounts and calls `/token/verify/`
- THEN the response is 200 with `{"valid": true}`
- AND the user remains on the current page

#### Scenario: Expired session on mount

- GIVEN an expired access token in memory
- WHEN the app mounts and calls `/token/verify/`
- THEN the response is 401
- AND the user is redirected to the login page
- AND the expired token is cleared from memory

#### Scenario: Network error on verify does not redirect

- GIVEN a valid access token in memory
- WHEN the app mounts and `/token/verify/` returns a network error
- THEN the user remains on the current page (no redirect)
- AND the error is logged to console

### Requirement: Remove Aggressive Silent Refresh

The frontend SHALL NOT perform automatic silent refresh on a fixed interval (e.g., 20 minutes). Session validity SHALL be determined by the verify endpoint on mount and by 401 responses triggering refresh.

#### Scenario: No interval-based refresh runs

- GIVEN the app is loaded
- WHEN the app is idle for 20 minutes
- THEN no automatic token refresh request is sent
- AND the access token expires naturally at 15 minutes

#### Scenario: 401 on mutating request triggers refresh

- GIVEN an expired access token
- WHEN a mutating request returns 401
- THEN the interceptor attempts a token refresh using the refresh token
- AND if refresh succeeds, the original request is retried
- AND if refresh fails, the user is redirected to login
