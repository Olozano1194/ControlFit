# Demo Request Soft Delete Specification

## Purpose

Implement soft delete pattern for demo requests, allowing cancellation without permanent data loss, maintaining audit trail and history.

## Requirements

### Requirement: Soft Delete Implementation

The system SHALL implement soft delete for `DemoRequest` by setting `estado='cancelada'` instead of hard delete. The `destroy()` method SHALL update the estado field, not remove the record.

#### Scenario: Soft delete sets estado to cancelada

- GIVEN a DemoRequest with `estado='pendiente'`
- WHEN calling `DELETE /demo-requests/{id}/`
- THEN the request is not removed from database
- AND `estado` is updated to `'cancelada'`
- AND response contains updated object with `estado='cancelada'`

#### Scenario: Soft delete preserves record

- GIVEN a DemoRequest with `estado='cancelada'`
- WHEN querying DemoRequest history
- THEN the cancelled request is still visible
- AND the request maintains its original data

### Requirement: Estado Transition Validation

The system SHALL validate estado transitions for soft delete. Only requests with `estado='pendiente'` or `estado='contactado'` can be cancelled. Already cancelled requests cannot be cancelled again.

#### Scenario: Cancel pending request

- GIVEN a DemoRequest with `estado='pendiente'`
- WHEN calling `DELETE /demo-requests/{id}/`
- THEN the request is cancelled successfully
- AND `estado` becomes `'cancelada'`

#### Scenario: Cancel contacted request

- GIVEN a DemoRequest with `estado='contactado'`
- WHEN calling `DELETE /demo-requests/{id}/`
- THEN the request is cancelled successfully
- AND `estado` becomes `'cancelada'`

#### Scenario: Cannot cancel already cancelled request

- GIVEN a DemoRequest with `estado='cancelada'`
- WHEN calling `DELETE /demo-requests/{id}/`
- THEN the request returns 400 Bad Request
- AND error indicates request is already cancelled

### Requirement: Serializer Validation

The system SHALL update `DemoRequestSerializer` to validate estado transitions. The serializer SHALL accept `cancelada` as a valid estado value for DELETE operations.

#### Scenario: Serializer accepts cancelada estado

- GIVEN a DemoRequestSerializer
- WHEN validating `estado='cancelada'`
- THEN validation passes
- AND the serializer allows the transition

#### Scenario: Serializer rejects invalid transitions

- GIVEN a DemoRequest with `estado='cancelada'`
- WHEN attempting to PATCH with `estado='contactado'`
- THEN validation fails
- AND error indicates invalid transition

### Requirement: Frontend Delete Button

The system SHALL add a delete button to `DemoRequestsPage.tsx` with confirmation modal. The button SHALL be visible for requests with `estado='pendiente'` or `estado='contactado'`. Clicking delete SHALL show confirmation modal before proceeding.

#### Scenario: Delete button visible for cancellable requests

- GIVEN a DemoRequest with `estado='pendiente'`
- WHEN viewing DemoRequestsPage
- THEN delete button is visible
- AND clicking shows confirmation modal

#### Scenario: Delete button hidden for cancelled requests

- GIVEN a DemoRequest with `estado='cancelada'`
- WHEN viewing DemoRequestsPage
- THEN delete button is not visible
- AND request shows cancelled status

#### Scenario: Confirmation modal flow

- GIVEN a user clicking delete button
- WHEN confirmation modal appears
- THEN user can confirm or cancel
- AND confirming triggers DELETE request
-AND success shows toast confirmation

### Requirement: API Response Format

The system SHALL return the updated DemoRequest object after soft delete. The response SHALL include `estado='cancelada'` and all other fields unchanged.

#### Scenario: DELETE returns updated object

- GIVEN a DemoRequest with `estado='pendiente'`
- WHEN calling `DELETE /demo-requests/{id}/`
- THEN response status is 200
- AND response body contains updated object
- AND object has `estado='cancelada'`
- AND all other fields are preserved

### Requirement: Frontend API Integration

The system SHALL update `demoRequests.api.ts` to include DELETE call. The API function SHALL send DELETE request to `/demo-requests/{id}/` and handle the response.

#### Scenario: API function sends DELETE request

- GIVEN a DemoRequest id
- WHEN calling the delete API function
- THEN DELETE request is sent to `/demo-requests/{id}/`
- AND response contains updated object

#### Scenario: API function handles errors

- GIVEN a DELETE request that fails
- WHEN the API function receives error response
- THEN error is propagated to caller
- AND appropriate error message is shown

## Test Requirements

### Unit Tests

- Test `DemoRequest.destroy()` sets `estado='cancelada'`
- Test serializer validates estado transitions
- Test cannot cancel already cancelled request
- Test delete button visibility based on estado

### Integration Tests

- Test DELETE endpoint returns updated object
- Test DELETE endpoint preserves record in database
- Test frontend delete flow with confirmation modal

### E2E Tests

- Test complete soft delete flow: cancel → verify → history
- Test cannot delete already cancelled request
- Test audit trail preserved after cancellation