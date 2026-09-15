# Token Verify Endpoint Specification

## Purpose

Provide a lightweight, read-only endpoint for frontend silent session validation. This replaces aggressive silent refresh intervals with a simpler check that tells the frontend whether the current access token is still valid.

## Requirements

### Requirement: Token Verification Endpoint

The system SHALL provide a `GET /gym/api/v1/token/verify/` endpoint. The endpoint SHALL accept a Bearer token in the Authorization header and return the token's validity status and expiration timestamp.

#### Scenario: Valid token returns 200 with validity info

- GIVEN a valid, non-expired access token `tok_valid`
- WHEN GETting `/gym/api/v1/token/verify/` with `Authorization: Bearer tok_valid`
- THEN the response is 200 OK
- AND the body is `{"valid": true, "exp": <unix_timestamp>}`

#### Scenario: Expired token returns 401

- GIVEN an expired access token `tok_expired`
- WHEN GETting `/gym/api/v1/token/verify/` with `Authorization: Bearer tok_expired`
- THEN the response is 401 Unauthorized
- AND the body is `{"valid": false}`

#### Scenario: Missing token returns 401

- GIVEN no Authorization header
- WHEN GETting `/gym/api/v1/token/verify/`
- THEN the response is 401 Unauthorized

#### Scenario: Malformed token returns 401

- GIVEN a malformed token string `not.a.jwt`
- WHEN GETting `/gym/api/v1/token/verify/` with `Authorization: Bearer not.a.jwt`
- THEN the response is 401 Unauthorized

### Requirement: Verify Endpoint is Read-Only

The endpoint SHALL NOT modify tokens, rotate refresh tokens, set cookies, or produce any side effects. It is a pure validation check.

#### Scenario: Verify does not rotate tokens

- GIVEN a valid refresh token and access token
- WHEN GETting `/gym/api/v1/token/verify/` with the access token
- THEN the original refresh token remains valid
- AND no new refresh token is issued

#### Scenario: Verify does not set cookies

- GIVEN a valid access token
- WHEN GETting `/gym/api/v1/token/verify/`
- THEN no Set-Cookie headers are present in the response

### Requirement: Verify Response Schema

The success response SHALL contain exactly `valid` (boolean) and `exp` (integer, Unix timestamp). The error response SHALL contain `detail` (string).

#### Scenario: Success response schema

- GIVEN a valid access token
- WHEN the verify endpoint processes the request
- THEN the response body has keys `valid` and `exp`
- AND `valid` is `true`
- AND `exp` is an integer representing a future Unix timestamp

#### Scenario: Error response schema

- GIVEN an invalid token
- WHEN the verify endpoint processes the request
- THEN the response body has key `detail`
- AND the response status is 401
