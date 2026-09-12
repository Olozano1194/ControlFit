# Platform Analytics Specification

## Purpose

Ensure platform dashboard analytics return numeric values as numbers, not strings, eliminating frontend type conversion workarounds.

## Requirements

### Requirement: Numeric Response Types

The system SHALL return numeric analytics fields as numbers (integers or floats) in API responses, not as strings. The `retencion_promedio` field SHALL be returned as a number with one decimal place.

#### Scenario: retencion_promedio returns number

- GIVEN a platform stats request
- WHEN the API returns `retencion_promedio`
- THEN the response type is number (not string)
- AND the value has one decimal place (e.g., `85.5` not `"85.5"`)

#### Scenario: Frontend receives number without conversion

- GIVEN the frontend receives `retencion_promedio` as number
- WHEN displaying the value
- THEN no `.toFixed()` conversion is needed
- AND the value displays correctly with one decimal place

### Requirement: DecimalField Configuration

The system SHALL configure `PlatformStatsSerializer.retencion_promedio` as `DecimalField(max_digits=5, decimal_places=1, coerce_to_string=False)`. This ensures the serializer returns a number instead of a string.

#### Scenario: Serializer returns number type

- GIVEN the `PlatformStatsSerializer` with `coerce_to_string=False`
- WHEN serializing `retencion_promedio`
- THEN the serialized value is a number
- AND the value is not wrapped in quotes

### Requirement: Frontend Type Handling

The system SHALL update `PlatformDashboardPage.tsx` to handle `retencion_promedio` as a number. The `.toFixed()` workaround SHALL be removed.

#### Scenario: Frontend displays numeric value directly

- GIVEN `stats.retencion_promedio` is a number (e.g., `85.5`)
- WHEN rendering in JSX
- THEN the value is displayed directly without `Number()` conversion
- AND the display shows one decimal place

### Requirement: Regression Prevention

The system SHALL include tests validating that `retencion_promedio` is returned as a number. Tests SHALL assert the response type is number, not string.

#### Scenario: Backend test validates number type

- GIVEN a platform stats API test
- WHEN the response includes `retencion_promedio`
- THEN the test asserts `isinstance(data['retencion_promedio'], (int, float))`
- AND the test does NOT assert string equality

#### Scenario: Frontend test validates number handling

- GIVEN a frontend component test for `PlatformDashboardPage`
- WHEN mocking platform stats with `retencion_promedio: 85.5`
- THEN the test expects numeric display without string conversion

## Test Requirements

### Unit Tests

- Test `PlatformStatsSerializer` returns `retencion_promedio` as number
- Test `PlatformStatsSerializer` with `coerce_to_string=False` configuration
- Test frontend component renders numeric value correctly

### Integration Tests

- Test API response contains `retencion_promedio` as number
- Test frontend receives and displays number without conversion
- Test regression: previously failing test now passes with number type

### E2E Tests

- Test platform dashboard displays retention percentage correctly
- Test no JavaScript errors from type conversion