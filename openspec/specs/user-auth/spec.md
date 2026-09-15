# User Auth Specification

## Purpose

Add end-to-end test for forced password change flow, verifying the complete lifecycle from login to password change to access restoration.

## Requirements

### Requirement: E2E Forced Password Change Test

The system SHALL provide an end-to-end test that covers the complete forced password change flow. The test SHALL verify login with `must_change_password=True`, denial of access to protected endpoints, successful password change, and restoration of access.

#### Scenario: Admin user forced password change flow

- GIVEN an admin user with `must_change_password=True`
- WHEN logging in with valid credentials
- THEN login succeeds and JWT token is obtained
- AND accessing a protected endpoint returns 403 Forbidden
- AND POSTing to `/password/change/` with valid old and new passwords returns 200
- AND accessing the same protected endpoint now returns 200

#### Scenario: Recepcion user forced password change flow

- GIVEN a recepcion user with `must_change_password=True`
- WHEN logging in with valid credentials
- THEN login succeeds and JWT token is obtained
- AND accessing a protected endpoint returns 403 Forbidden
- AND POSTing to `/password/change/` with valid old and new passwords returns 200
- AND accessing the same protected endpoint now returns 200

### Requirement: JWT Cookie Flow

The system SHALL test the JWT cookie-based authentication flow. The test SHALL use Django test client with cookie handling to simulate real browser behavior.

#### Scenario: JWT token obtained via login

- GIVEN a user with valid credentials
- WHEN POSTing to `/gym/api/v1/token/`
- THEN response contains access token
- AND refresh token cookie is set

#### Scenario: Protected endpoint requires valid token

- GIVEN a JWT access token
- WHEN accessing a protected endpoint with the token
- THEN the endpoint returns 200 (if authorized)
- AND the endpoint returns 403 (if must_change_password=True)

### Requirement: Password Change Endpoint

The system SHALL test the password change endpoint at `POST /auth/password/change/`. The endpoint SHALL accept old_password, new_password, and confirm_password fields. Successful change SHALL reset `must_change_password` to False.

#### Scenario: Successful password change

- GIVEN a user with `must_change_password=True`
- WHEN POSTing to `/auth/password/change/` with valid old_password and matching new passwords
- THEN response is 200
- AND `must_change_password` becomes False
- AND new password works for subsequent logins

#### Scenario: Invalid old password fails

- GIVEN a user with `must_change_password=True`
- WHEN POSTing to `/auth/password/change/` with incorrect old_password
- THEN response is 400
- AND `must_change_password` remains True

### Requirement: Access Restoration

The system SHALL verify that after successful password change, the user can access protected endpoints. The `must_change_password` flag SHALL be False after password change.

#### Scenario: Access restored after password change

- GIVEN a user who just changed password (`must_change_password=False`)
- WHEN accessing a protected endpoint
- THEN the endpoint returns 200
- AND no 403 Forbidden is returned

## Test Requirements

### Unit Tests

- Test `must_change_password` flag is True after user creation
- Test `must_change_password` flag is False after password change
- Test password change endpoint validates old password

### Integration Tests

- Test login returns JWT token
- Test protected endpoint returns 403 when `must_change_password=True`
- Test password change resets `must_change_password` flag
- Test access restored after password change

### E2E Tests

- Test complete flow: login → 403 → password change → 200 access
- Test both admin and recepcion roles
- Test JWT cookie flow with Django test client