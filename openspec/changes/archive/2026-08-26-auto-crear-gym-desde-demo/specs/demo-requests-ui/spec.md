# Demo Requests UI Specification

## Purpose

Update the frontend DemoRequestsPage to handle gym provisioning responses, show loading states, and surface specific errors.

## Requirements

### Requirement: Gym-Aware Toast

The system SHALL display a specific toast when gym_creado is present in the PATCH response.

#### Scenario: gym created toast

- GIVEN a DemoRequest PATCH response includes gym_creado
- WHEN the toast is displayed
- THEN the message is 'Gimnasio creado, credenciales enviadas al lead'
- AND the page does NOT navigate away

#### Scenario: generic estado toast

- GIVEN a DemoRequest PATCH response does NOT include gym_creado
- WHEN the toast is displayed
- THEN the message is 'Marcado como [estado]'

### Requirement: Loading State on Badge

The system SHALL show a loading indicator on the badge during the PATCH request.

#### Scenario: badge loading

- GIVEN the user clicks the estado badge
- WHEN the PATCH request is in flight
- THEN the badge shows a spinner or disabled state
- AND further clicks are ignored until the request completes

### Requirement: Error Handling

The system SHALL display specific error toasts based on the response status.

#### Scenario: duplicate email error

- GIVEN the PATCH response is 400 with email duplicado
- WHEN the error toast is displayed
- THEN the message indicates the email is already registered

#### Scenario: generic error

- GIVEN the PATCH response is a non-400 error
- WHEN the error toast is displayed
- THEN the message is 'No se pudo actualizar el estado'
