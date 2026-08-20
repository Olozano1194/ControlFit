# calendario-eventos-frontend Specification

## Purpose

Provides complete event CRUD UX in the calendar module: modal create/edit via EventoForm, slot-click prefill, drag-and-drop persistence, admin-only delete, and role-based visibility for reception users.

## Requirements

### Requirement: Event Creation via Modal

The system SHALL display a "+ Nuevo Evento" button in the calendar header that opens EventoForm modal in create mode. The modal SHALL include fields for title, start/end datetime, description, event type, and optional relation.

#### Scenario: Admin creates event via header button

- GIVEN the user is authenticated as admin
- WHEN the user clicks "+ Nuevo Evento" button
- THEN EventoForm modal opens in create mode with empty fields
- AND the modal shows a "Crear Evento" submit button

#### Scenario: Reception creates event via header button

- GIVEN the user is authenticated as reception
- WHEN the user clicks "+ Nuevo Evento" button
- THEN EventoForm modal opens in create mode with empty fields
- AND the modal shows a "Crear Evento" submit button

#### Scenario: Event creation succeeds

- GIVEN EventoForm modal is open in create mode
- WHEN the user fills required fields (title, start, end) and submits
- THEN the system calls createEvento API
- AND shows success toast "Evento creado correctamente"
- AND closes the modal
- AND refetches calendar events to display the new event

#### Scenario: Event creation fails with API error

- GIVEN EventoForm modal is open in create mode
- WHEN the user submits and the API returns an error
- THEN the system shows error toast with the error message
- AND the modal remains open for correction

### Requirement: Event Editing via Detail Modal

The system SHALL open EventoForm modal in edit mode when the user clicks "Editar" in the event detail modal. The form SHALL be pre-filled with the existing event data.

#### Scenario: Admin edits event

- GIVEN the user is authenticated as admin
- AND an event detail modal is open
- WHEN the user clicks "Editar" button
- THEN EventoForm modal opens in edit mode
- AND fields are pre-filled with the event's current data
- AND the modal shows an "Actualizar" submit button

#### Scenario: Reception edits event

- GIVEN the user is authenticated as reception
- AND an event detail modal is open
- WHEN the user clicks "Editar" button
- THEN EventoForm modal opens in edit mode
- AND fields are pre-filled with the event's current data

#### Scenario: Event update succeeds

- GIVEN EventoForm modal is open in edit mode
- WHEN the user modifies fields and submits
- THEN the system calls updateEvento API
- AND shows success toast "Evento actualizado correctamente"
- AND closes the modal
- AND refetches calendar events

### Requirement: Slot-Click Prefill for Event Creation

The system SHALL open EventoForm modal in create mode when the user clicks an empty time slot in the calendar. The start and end datetime fields SHALL be pre-filled based on the clicked slot.

#### Scenario: Click on empty slot in month view

- GIVEN the calendar is in month view
- WHEN the user clicks on an empty day cell
- THEN EventoForm modal opens in create mode
- AND fecha_inicio is set to the start of the clicked day (00:00)
- AND fecha_fin is set to the end of the clicked day (23:59)

#### Scenario: Click on empty slot in week/day view

- GIVEN the calendar is in week or day view
- WHEN the user clicks on an empty time slot
- THEN EventoForm modal opens in create mode
- AND fecha_inicio is set to the clicked slot start time
- AND fecha_fin is set to one hour after the start time

### Requirement: Drag-and-Drop Event Persistence

The system SHALL support drag-and-drop to reschedule events and resize to change duration. Changes SHALL be persisted automatically via updateEvento API without explicit save action.

#### Scenario: Admin drags event to new time

- GIVEN the user is authenticated as admin
- AND the calendar displays events
- WHEN the user drags an event to a different time slot
- THEN the system calls updateEvento API with new fecha_inicio and fecha_fin
- AND refetches calendar events to reflect the change

#### Scenario: Admin resizes event duration

- GIVEN the user is authenticated as admin
- AND the calendar displays events
- WHEN the user resizes an event by dragging its edge
- THEN the system calls updateEvento API with updated fecha_fin
- AND refetches calendar events

#### Scenario: Drag-and-drop fails with API error

- GIVEN the user drags or resizes an event
- WHEN the updateEvento API call fails
- THEN the system shows error toast with the error message
- AND the event reverts to its original position visually

#### Scenario: Reception user cannot drag events

- GIVEN the user is authenticated as reception
- AND the calendar displays events
- WHEN the user attempts to drag an event
- THEN the drag operation is not initiated (no visual feedback)

### Requirement: Admin-Only Event Deletion

The system SHALL allow only admin users to delete events. The delete button SHALL be hidden from reception users. Deletion SHALL require confirmation via window.confirm.

#### Scenario: Admin deletes event

- GIVEN the user is authenticated as admin
- AND an event detail modal is open
- WHEN the user clicks "Eliminar" button
- THEN window.confirm shows "¿Eliminar este evento?"
- AND if confirmed, the system calls deleteEvento API
- AND shows success toast "Evento eliminado correctamente"
- AND closes the detail modal
- AND refetches calendar events

#### Scenario: Admin cancels deletion

- GIVEN the user is authenticated as admin
- AND an event detail modal is open
- WHEN the user clicks "Eliminar" and cancels the confirmation
- THEN no API call is made
- AND the detail modal remains open

#### Scenario: Reception user does not see delete button

- GIVEN the user is authenticated as reception
- AND an event detail modal is open
- THEN the "Eliminar" button is not rendered

#### Scenario: Event deletion fails with API error

- GIVEN the user confirms event deletion
- WHEN the deleteEvento API call fails
- THEN the system shows error toast with the error message
- AND the detail modal remains open

### Requirement: Calendar Event Display with Type Colors

The system SHALL display events in the calendar with background colors matching their assigned TipoEvento. Events without a type SHALL use a default color.

#### Scenario: Event with assigned type

- GIVEN an event has a tipo_detalle with color "#FF5733"
- WHEN the calendar renders the event
- THEN the event block has background color "#FF5733"

#### Scenario: Event without type

- GIVEN an event has tipo null
- WHEN the calendar renders the event
- THEN the event block has default background color "#3B82F6"

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