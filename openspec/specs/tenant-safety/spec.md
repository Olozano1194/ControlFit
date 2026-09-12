# Tenant Safety Specification

## Purpose

Implement default filtering for multi-tenant models to ensure inactive records are excluded from standard queries, preventing accidental data leakage.

## Requirements

### Requirement: ActiveManager Implementation

The system SHALL provide an `ActiveManager` class that filters queries to return only records where `is_active=True`. The manager SHALL override `get_queryset()` to apply this filter by default.

#### Scenario: ActiveManager filters inactive records

- GIVEN an `ActiveManager` instance
- WHEN calling `get_queryset()`
- THEN the queryset filters `is_active=True`
- AND inactive records are excluded

#### Scenario: ActiveManager preserves default manager behavior

- GIVEN an `ActiveManager` instance
- WHEN calling standard queryset methods (filter, exclude, get)
- THEN the methods work as expected
- AND the `is_active=True` filter is applied

### Requirement: Gimnasio Active Filtering

The system SHALL configure `Gimnasio` model with `ActiveManager` as default manager. `Gimnasio.objects` SHALL return only active gyms. `Gimnasio.all_objects` SHALL return all gyms regardless of active status.

#### Scenario: Gimnasio.objects excludes inactive

- GIVEN inactive gyms (is_active=False)
- WHEN calling `Gimnasio.objects.all()`
- THEN only active gyms are returned
- AND inactive gyms are excluded

#### Scenario: Gimnasio.all_objects includes all

- GIVEN both active and inactive gyms
- WHEN calling `Gimnasio.all_objects.all()`
- THEN all gyms are returned
- AND both active and inactive are included

#### Scenario: Admin uses all_objects

- GIVEN the Django admin for Gimnasio
- WHEN displaying gyms in admin
- THEN all gyms are shown (active and inactive)
- AND admin can manage inactive gyms

### Requirement: Usuario Active Filtering

The system SHALL configure `Usuario` model with `ActiveManager` as default manager. `Usuario.objects` SHALL return only active users. `Usuario.all_objects` SHALL return all users regardless of active status.

#### Scenario: Usuario.objects excludes inactive

- GIVEN inactive users (is_active=False)
- WHEN calling `Usuario.objects.all()`
- THEN only active users are returned
- AND inactive users are excluded

#### Scenario: Usuario.all_objects includes all

- GIVEN both active and inactive users
- WHEN calling `Usuario.all_objects.all()`
- THEN all users are returned
- AND both active and inactive are included

#### Scenario: Authentication uses active users only

- GIVEN a login attempt with inactive user credentials
- WHEN authenticating via `Usuario.objects`
- THEN authentication fails
- AND inactive users cannot log in

### Requirement: Code Audit

The system SHALL audit all `.objects` usages in views and services to ensure they use the correct manager. Admin views SHALL use `all_objects` where needed to show inactive records.

#### Scenario: Views use appropriate manager

- GIVEN views that query Gimnasio or Usuario
- WHEN the view needs only active records
- THEN it uses `.objects` (ActiveManager)
- AND when it needs all records (admin), it uses `.all_objects`

#### Scenario: No accidental inactive access

- GIVEN a view that should only show active records
- WHEN using `.objects.all()`
- THEN inactive records are excluded
- AND no data leakage occurs

### Requirement: Migration Safety

The system SHALL ensure the manager change does not require database migrations. Managers are Python-level constructs and do not affect database schema.

#### Scenario: No migration required

- GIVEN the ActiveManager implementation
- WHEN running `python makemigrations`
- THEN no migrations are generated
- AND the change is purely Python-level

## Test Requirements

### Unit Tests

- Test `ActiveManager.get_queryset()` filters `is_active=True`
- Test `Gimnasio.objects.all()` excludes inactive gyms
- Test `Gimnasio.all_objects.all()` includes all gyms
- Test `Usuario.objects.all()` excludes inactive users
- Test `Usuario.all_objects.all()` includes all users

### Integration Tests

- Test admin displays all records (active and inactive)
- Test views using `.objects` only see active records
- Test authentication fails for inactive users

### E2E Tests

- Test full application flow with active/inactive records
- Test no data leakage across tenant boundaries