# calendario-tipos-frontend Specification

## Purpose

Provides admin-only TipoEvento management from the calendar screen via a modal interface. Allows admin users to create, edit, and delete event types without leaving the calendar context.

## Requirements

### Requirement: Admin-Only TipoEvento Management Button

The system SHALL display a "Gestionar Tipos" button in the calendar header, visible only to admin users. The button SHALL open TipoEventoAdmin modal.

#### Scenario: Admin sees tipos button

- GIVEN the user is authenticated as admin
- AND the calendar page is loaded
- THEN a "Gestionar Tipos" button is visible in the header section

#### Scenario: Reception does not see tipos button

- GIVEN the user is authenticated as reception
- AND the calendar page is loaded
- THEN the "Gestionar Tipos" button is not rendered

#### Scenario: Admin opens tipos modal

- GIVEN the user is authenticated as admin
- WHEN the user clicks "Gestionar Tipos" button
- THEN TipoEventoAdmin modal opens as an overlay

### Requirement: TipoEvento CRUD in Modal

The system SHALL provide full CRUD operations for TipoEvento within the TipoEventoAdmin modal. The modal SHALL display a list of types with edit/delete actions and a create button.

#### Scenario: Admin views tipos list

- GIVEN the user is authenticated as admin
- AND the TipoEventoAdmin modal is open
- THEN a table of TipoEvento items is displayed
- AND each row shows color swatch, name, and action buttons (edit, delete)

#### Scenario: Admin creates new tipo

- GIVEN the TipoEventoAdmin modal is open
- WHEN the user clicks "Nuevo Tipo" button
- THEN TipoEventoForm modal opens in create mode
- AND after successful creation, the tipos list refreshes
- AND success toast "Tipo creado correctamente" is shown

#### Scenario: Admin edits existing tipo

- GIVEN the TipoEventoAdmin modal is open
- AND the tipos list is displayed
- WHEN the user clicks edit button on a tipo row
- THEN TipoEventoForm modal opens in edit mode with pre-filled data
- AND after successful update, the tipos list refreshes
- AND success toast "Tipo actualizado correctamente" is shown

#### Scenario: Admin deletes tipo

- GIVEN the TipoEventoAdmin modal is open
- AND the tipos list is displayed
- WHEN the user clicks delete button on a tipo row
- THEN window.confirm shows "¿Eliminar el tipo "{nombre}"?"
- AND if confirmed, the system calls deleteTipoEvento API
- AND the tipos list refreshes
- AND success toast "Tipo eliminado correctly" is shown

#### Scenario: Admin cancels tipo deletion

- GIVEN the user clicks delete button on a tipo row
- WHEN the user cancels the confirmation dialog
- THEN no API call is made
- AND the tipos list remains unchanged

#### Scenario: Tipo deletion fails with 409 conflict

- GIVEN the user confirms tipo deletion
- WHEN the API returns 409 (tipo has associated events)
- THEN the system shows error toast "No se puede eliminar: el tipo tiene eventos asociados"

### Requirement: TipoEvento Form Validation

The TipoEventoForm SHALL validate required fields (nombre, color) and enforce length constraints. Duplicate names SHALL be rejected by the backend with a 400 error.

#### Scenario: Submit with empty name

- GIVEN TipoEventoForm is open
- WHEN the user submits with empty nombre field
- THEN validation error "El nombre es requerido" is displayed

#### Scenario: Submit with duplicate name

- GIVEN TipoEventoForm is open
- WHEN the user submits with a nombre that already exists
- THEN the API returns 400
- AND error toast "Ya existe un tipo con ese nombre en este gimnasio" is shown

### Requirement: TipoEvento Color Preview

The TipoEventoForm SHALL display a live color preview as the user selects a color via the color picker.

#### Scenario: Color preview updates on selection

- GIVEN TipoEventoForm is open
- WHEN the user selects a new color via the color picker
- THEN the preview swatch updates to show the selected color
- AND the hex code is displayed next to the picker

### Requirement: Calendar Refresh After Tipo Changes

Changes to TipoEvento (create, edit, delete) SHALL trigger a refresh of the calendar's tipo list so that event colors and type dropdowns reflect the latest data.

#### Scenario: Tipo created, calendar types refresh

- GIVEN the calendar page is open
- WHEN the user creates a new tipo via TipoEventoAdmin
- THEN the calendar's internal tipo list is updated
- AND new events can use the newly created type

#### Scenario: Tipo deleted, calendar types refresh

- GIVEN the calendar page is open
- WHEN the user deletes a tipo via TipoEventoAdmin
- THEN the calendar's internal tipo list is updated
- AND events previously using the deleted type show no type assignment