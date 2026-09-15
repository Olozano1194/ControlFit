# CSRF Protection Specification

## Purpose

Add explicit CSRF protection via double-submit cookie pattern. This provides defense-in-depth beyond SameSite cookies, protecting against subdomain attacks and scenarios where SameSite is insufficient.

## Requirements

### Requirement: CSRF Cookie on Authentication

The system SHALL set a CSRF cookie on login and refresh responses. The cookie SHALL be readable by JavaScript (HttpOnly=false), SHALL use SameSite=Lax in development, SameSite=None + Secure in production, and SHALL be scoped to the API path `/gym/api/v1/`.

#### Scenario: Login response sets CSRF cookie

- GIVEN a user with valid credentials
- WHEN POSTing to `/gym/api/v1/token/` (login)
- THEN the response sets a cookie named `csrftoken`
- AND the cookie HttpOnly attribute is false
- AND the cookie path is `/gym/api/v1/`

#### Scenario: Refresh response sets CSRF cookie

- GIVEN a valid refresh token
- WHEN POSTing to `/gym/api/v1/token/refresh/`
- THEN the response sets a cookie named `csrftoken`
- AND the cookie HttpOnly attribute is false

#### Scenario: CSRF cookie SameSite in development

- GIVEN the server runs with `DEBUG=True`
- WHEN any response sets the CSRF cookie
- THEN the SameSite attribute is `Lax`

#### Scenario: CSRF cookie SameSite in production

- GIVEN the server runs with `DEBUG=False`
- WHEN any response sets the CSRF cookie
- THEN the SameSite attribute is `None`
- AND the Secure attribute is true

### Requirement: CSRF Header Validation on Mutating Requests

The system SHALL require an `X-CSRF-Token` header on all mutating requests (POST, PUT, PATCH, DELETE). The header value MUST match the `csrftoken` cookie value. Requests without the header or with a mismatch SHALL receive 403 Forbidden.

#### Scenario: POST with valid CSRF header succeeds

- GIVEN a valid access token and a `csrftoken` cookie value `abc123`
- WHEN POSTing with header `X-CSRF-Token: abc123`
- THEN the request is processed normally (not rejected by CSRF)

#### Scenario: POST without CSRF header returns 403

- GIVEN a valid access token
- WHEN POSTing without the `X-CSRF-Token` header
- THEN the response is 403 Forbidden
- AND the response body contains `{"detail": "CSRF token missing."}`

#### Scenario: POST with mismatched CSRF header returns 403

- GIVEN a valid access token and a `csrftoken` cookie value `abc123`
- WHEN POSTing with header `X-CSRF-Token: wrong_token`
- THEN the response is 403 Forbidden

#### Scenario: GET requests bypass CSRF validation

- GIVEN a valid access token
- WHEN sending a GET request
- THEN the request is processed without CSRF validation
- AND no 403 is returned for missing CSRF header

#### Scenario: PUT/PATCH/DELETE require CSRF header

- GIVEN a valid access token and a `csrftoken` cookie
- WHEN sending PUT, PATCH, or DELETE requests
- THEN the `X-CSRF-Token` header is required
- AND requests without the header return 403

### Requirement: CSRF Cookie Path Scoping

The CSRF cookie SHALL be scoped to the API base path `/gym/api/v1/` to avoid leaking to non-API routes.

#### Scenario: CSRF cookie scoped to API path

- GIVEN the server sets a CSRF cookie
- WHEN inspecting the Set-Cookie header
- THEN the Path attribute is `/gym/api/v1/`
