# Demo Gym Onboarding Specification

## Purpose

Automatically provision a Gimnasio and admin Usuario when a SuperAdmin transitions a DemoRequest from `pendiente` to `contactado`. Ensures atomic creation, idempotency, and graceful handling of edge cases.

## Requirements

### Requirement: Atomic Gym+Admin Provisioning

The system SHALL atomically create a Gimnasio and an admin Usuario when a DemoRequest transitions from `pendiente` to `contactado` and `gym_creado` is NULL.

#### Scenario: Happy path — pendiente to contactado

- GIVEN a DemoRequest with estado=pendiente and gym_creado=NULL
- WHEN a SuperAdmin PATCHes estado to contactado
- THEN a Gimnasio is created with name from nombre_gimnasio, phone from telefono
- AND an admin Usuario is created with email from DemoRequest.email, roles=admin, must_change_password=True
- AND DemoRequest.gym_creado links to the new Gimnasio
- AND the response includes gym_creado info (id, name)

#### Scenario: Idempotency — already contactado

- GIVEN a DemoRequest with estado=contactado and gym_creado already set
- WHEN a SuperAdmin PATCHes estado to contactado again
- THEN no duplicate Gimnasio or Usuario is created
- AND the existing gym_creado info is returned

#### Scenario: Reverso — contactado to pendiente

- GIVEN a DemoRequest with estado=contactado and gym_creado set
- WHEN a SuperAdmin PATCHes estado to pendiente
- THEN gym_creado.is_active is set to False
- AND the linked admin Usuario.is_active is set to False
- AND DemoRequest.gym_creado is set to NULL

### Requirement: Admin Profile Convention

The system SHALL set the admin Usuario name to 'Admin' and lastname to the first 50 characters of nombre_gimnasio.

#### Scenario: lastname truncation

- GIVEN nombre_gimnasio is 'Gimnasio Fitness Center Bogota Colombia'
- WHEN admin Usuario is created
- THEN Usuario.lastname is 'Gimnasio Fitness Center Bogota Colombia' (45 chars, under 50)

#### Scenario: lastname exceeds 50 chars

- GIVEN nombre_gimnasio is 'Gimnasio Fitness Center Bogota Colombia Sur America'
- WHEN admin Usuario is created
- THEN Usuario.lastname is truncated to 50 characters

### Requirement: Duplicate Email Rejection

The system SHALL return 400 if the DemoRequest email already exists in the Usuario table.

#### Scenario: email already exists

- GIVEN a DemoRequest with email='existing@gym.com'
- AND a Usuario with email='existing@gym.com' already exists
- WHEN a SuperAdmin PATCHes estado to contactado
- THEN the response is 400 with message indicating the email is already registered
- AND no Gimnasio or Usuario is created

### Requirement: Phone Validation

The system SHALL truncate telefono to 20 characters max when creating the Gimnasio.

#### Scenario: phone exceeds 20 chars

- GIVEN telefono is '+57 300 123 4567 ext 8901234'
- WHEN Gimnasio is created
- THEN Gimnasio.phone is truncated to 20 characters

### Requirement: Auth Guard

The system SHALL require SuperAdmin authentication for the PATCH endpoint.

#### Scenario: unauthenticated user

- GIVEN no auth token
- WHEN PATCH /solicitudes-demo/{id}/
- THEN response is 401

#### Scenario: non-superadmin user

- GIVEN a authenticated user with roles=admin
- WHEN PATCH /solicitudes-demo/{id}/
- THEN response is 403
