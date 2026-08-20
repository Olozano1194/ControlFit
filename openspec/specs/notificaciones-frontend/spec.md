# notificaciones-frontend Specification

## Purpose

Frontend notification UI: bell menu with real unread badge, notifications page with per-item read and mark-all, updated model/API client, and calendar deep link integration.

## Requirements

### Requirement: Notification Model and API Client

The system SHALL provide a TypeScript `Notification` interface with fields: `id`, `tipo`, `titulo`, `mensaje`, `fecha`, `link`, `whatsapp_link?`, `relacion_tipo`, `relacion_id`, `is_read`, `read_at`, `created_at`. The API client SHALL provide: `getNotifications()`, `getUnreadCount()`, `markOneRead(id)`, `markAllAsRead()`.

#### Scenario: API contract matches backend

- GIVEN the backend returns a notification list
- WHEN the frontend parses the response
- THEN each item conforms to the Notification interface
- AND `id` is present for stable keys

### Requirement: NotificationMenu Real Badge

The NotificationMenu SHALL display a real unread count from `getUnreadCount()` (not the list length). Polling SHALL continue every 5 minutes. Per-item read action SHALL call `markOneRead(id)` and update local state.

#### Scenario: Badge shows unread count

- GIVEN there are 3 unread notifications
- WHEN the NotificationMenu loads
- THEN the badge shows "3"

#### Scenario: Badge updates after read

- GIVEN the badge shows "3"
- WHEN the user clicks a notification and marks it read
- THEN the badge decrements to "2"

#### Scenario: Empty state

- GIVEN there are 0 unread notifications
- WHEN the NotificationMenu loads
- THEN the badge is hidden
- AND the dropdown shows "No hay notificaciones nuevas"

### Requirement: NotificationMenu Per-Item Read

The NotificationMenu SHALL call `markOneRead(id)` when a notification is clicked. The notification SHALL disappear from the list after read. WhatsApp link button SHALL remain functional.

#### Scenario: Click notification marks read

- GIVEN an unread notification in the menu
- WHEN the user clicks the notification
- THEN `markOneRead(id)` is called
- AND the notification is removed from the menu list

#### Scenario: WhatsApp button does not trigger read

- GIVEN a notification with whatsapp_link
- WHEN the user clicks the WhatsApp button
- THEN `markOneRead(id)` is NOT called
- AND the wa.me link opens in new tab

### Requirement: NotificationsPage List

The NotificationsPage SHALL fetch notifications via `getNotifications()` and display them in a list. Each item SHALL have a read action button. "Marcar todas como leídas" button SHALL call `markAllAsRead()`. Stable React keys SHALL use `n.id`.

#### Scenario: Page loads with notifications

- GIVEN the user navigates to `/dashboard/notifications`
- WHEN the page loads
- THEN a list of unread notifications is displayed
- AND each item has a read button

#### Scenario: Mark all read

- GIVEN the page shows 5 unread notifications
- WHEN the user clicks "Marcar todas como leídas"
- THEN `markAllAsRead()` is called
- AND the list becomes empty
- AND success toast is shown

#### Scenario: Empty state

- GIVEN there are no unread notifications
- WHEN the page loads
- THEN a "No hay notificaciones" message is displayed

### Requirement: Membership Notification Link Fix

Membership notifications SHALL link to `/dashboard/asignar-membresia-list` (not the deleted detail route). This fixes the pre-existing 404 bug.

#### Scenario: Membership notification link resolves

- GIVEN a membership notification with tipo='por_vencer'
- WHEN the user clicks the notification link
- THEN navigation goes to `/dashboard/asignar-membresia-list`
- AND no 404 error occurs

### Requirement: Calendar Deep Link

The CalendarioPage SHALL read `?evento=<id>` from URL query parameters. If present, it SHALL call `getEvento(id)` and open the existing detail modal with the fetched event as `selectedEvent`.

#### Scenario: Deep link opens event detail

- GIVEN the user navigates to `/dashboard/calendar?evento=123`
- WHEN the CalendarioPage loads
- THEN `getEvento(123)` is called
- AND the detail modal opens with event id=123

#### Scenario: No deep link parameter

- GIVEN the user navigates to `/dashboard/calendar` (no query param)
- WHEN the CalendarioPage loads
- THEN no automatic modal opens
- AND normal calendar behavior proceeds

### Requirement: Loading and Error States

The NotificationMenu and NotificationsPage SHALL show loading indicators during fetch. Errors SHALL be displayed via toast. The system SHALL NOT crash on API failures.

#### Scenario: Loading state

- GIVEN the notification list is being fetched
- WHEN the component is rendering
- THEN a loading spinner is displayed

#### Scenario: Error state

- GIVEN the API returns an error
- WHEN the fetch fails
- THEN an error toast is shown
- AND the component remains functional (no crash)

### Requirement: Polling Cadence

The NotificationMenu SHALL poll for unread count every 5 minutes (300000ms). The NotificationsPage SHALL NOT poll (fetch on mount only).

#### Scenario: Menu polls every 5 minutes

- GIVEN the NotificationMenu is mounted
- WHEN 5 minutes elapse
- THEN `getUnreadCount()` is called again

#### Scenario: Page does not poll

- GIVEN the NotificationsPage is mounted
- WHEN time passes
- THEN no additional fetch calls are made (only initial fetch)