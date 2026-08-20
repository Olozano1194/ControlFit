# Delta for calendario-eventos-frontend

## ADDED Requirements

### Requirement: Calendar Deep Link via Query Parameter

The system SHALL read `?evento=<id>` from the URL query parameters when CalendarioPage mounts. If present, the system SHALL call `getEvento(id)` to fetch the event and open the existing detail modal with the fetched event as `selectedEvent`. This enables deep linking from notification links.

#### Scenario: Deep link opens event detail

- GIVEN the user navigates to `/dashboard/calendar?evento=123`
- WHEN the CalendarioPage loads
- THEN `getEvento(123)` is called
- AND the detail modal opens with event id=123

#### Scenario: Invalid event ID in deep link

- GIVEN the user navigates to `/dashboard/calendar?evento=999`
- WHEN `getEvento(999)` returns 404
- THEN an error toast is shown
- AND the calendar loads normally without modal

#### Scenario: No deep link parameter

- GIVEN the user navigates to `/dashboard/calendar` (no query param)
- WHEN the CalendarioPage loads
- THEN no automatic modal opens
- AND normal calendar behavior proceeds

#### Scenario: Deep link with existing calendar data

- GIVEN the calendar is already loaded with events
- WHEN `?evento=123` is present
- THEN `getEvento(123)` is called
- AND the detail modal opens with the fetched event (even if not in initial calendar range)

## MODIFIED Requirements

### Requirement: Calendar Data Loading

The system SHALL fetch events and types on mount and display a loading indicator during fetch. Errors SHALL be shown via toast. The system SHALL also check for `?evento=<id>` query parameter and fetch that event if present.

(Previously: The system SHALL fetch events and types on mount and display a loading indicator during fetch. Errors SHALL be shown via toast.)

#### Scenario: Successful data load

- GIVEN the calendar page mounts
- WHEN the API returns events and types
- THEN the calendar renders all events with correct colors

#### Scenario: Data load fails

- GIVEN the calendar page mounts
- WHEN the API returns an error
- THEN the system shows error toast "Error al cargar datos del calendario"
- AND displays empty calendar state

#### Scenario: Deep link event fetch after calendar load

- GIVEN the calendar page mounts with `?evento=123`
- WHEN the API returns events and types
- THEN `getEvento(123)` is called
- AND the detail modal opens with the fetched event