# Token Lifetimes Specification

## Purpose

Reduce JWT token exposure windows to limit the impact of token leakage. Shorter lifetimes force more frequent refresh, reducing the time a stolen token remains usable.

## Requirements

### Requirement: Access Token Lifetime

The system SHALL configure SIMPLE_JWT `ACCESS_TOKEN_LIFETIME` to 15 minutes. Access tokens issued after deployment SHALL expire after 15 minutes.

#### Scenario: Access token expires after 15 minutes

- GIVEN a valid access token issued at T=0
- WHEN the token is presented at T=15:01 minutes
- THEN the endpoint returns 401 Unauthorized
- AND the response body contains `{"code": "token_not_valid"}`

#### Scenario: Access token valid within 15 minutes

- GIVEN a valid access token issued at T=0
- WHEN the token is presented at T=14:59 minutes
- THEN the endpoint returns 200 (or appropriate success)

#### Scenario: Previously issued 30-minute token remains valid

- GIVEN an access token issued BEFORE deployment with 30-minute lifetime
- WHEN the token is presented at T=20:00 minutes (past new limit, within old limit)
- THEN the endpoint returns 200 (no immediate revocation of old tokens)

### Requirement: Refresh Token Lifetime

The system SHALL configure SIMPLE_JWT `REFRESH_TOKEN_LIFETIME` to 3 days (72 hours). Refresh tokens issued after deployment SHALL expire after 3 days.

#### Scenario: Refresh token expires after 3 days

- GIVEN a valid refresh token issued at T=0
- WHEN the token is used to refresh at T=3 days + 1 second
- THEN the endpoint returns 401 Unauthorized

#### Scenario: Refresh token valid within 3 days

- GIVEN a valid refresh token issued at T=0
- WHEN the token is used to refresh at T=2 days 23 hours
- THEN a new access token is returned (200)

#### Scenario: Previously issued 7-day refresh token remains valid

- GIVEN a refresh token issued BEFORE deployment with 7-day lifetime
- WHEN the token is used to refresh at T=5 days (past new limit, within old limit)
- THEN a new access token is returned (no immediate revocation)

### Requirement: Token Rotation on Refresh

The system SHALL rotate the refresh token on each use. The response SHALL contain both a new access token and a new refresh token.

#### Scenario: Refresh rotation produces new tokens

- GIVEN a valid refresh token `old_refresh`
- WHEN POSTing to `/token/refresh/` with `old_refresh`
- THEN the response contains a new access token
- AND the response contains a new refresh token
- AND `old_refresh` is invalidated (cannot be reused)
