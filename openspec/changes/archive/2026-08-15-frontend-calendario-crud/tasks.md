# Tasks: Frontend Calendar CRUD (Nivel 1)

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~265 (CalendarioPage ~250, EventoForm ~8, SideBarUser 1) |
| 400-line budget risk | Low |
| Chained PRs recommended | No |
| Suggested split | Single PR |
| Delivery strategy | ask-on-risk |
| Chain strategy | pending |

Decision needed before apply: No
Chained PRs recommended: No
Chain strategy: size-exception
400-line budget risk: Low

## Phase 1: EventoForm — initialDates Prop

- [x] 1.1 Add `initialDates?: { start: string; end: string }` to `EventoFormProps` interface in `EventoForm.tsx`
- [x] 1.2 Update `EventoForm` destructuring to accept `initialDates`
- [x] 1.3 In the existing `useEffect` reset (line 69-92), when `event` is null and `initialDates` is provided, set `fecha_inicio` and `fecha_fin` from `initialDates` instead of empty strings. Slice to `datetime-local` format (`YYYY-MM-DDTHH:mm`)
- [x] 1.4 Verify: `tsc --noEmit` passes with no errors

## Phase 2: CalendarioPage — Imports, State, Helpers

- [x] 2.1 Add imports: `withDragAndDrop` from `react-big-calendar/lib/addons/dragAndDrop`, `useAuth`, `createEvento`/`updateEvento`/`deleteEvento` from API, `EventoForm`/`TipoEventoAdmin` components
- [x] 2.2 Add `import 'react-big-calendar/lib/addons/dragAndDrop/styles.css'`
- [x] 2.3 Add state variables: `isEventoFormOpen`, `editingEvent`, `isTipoAdminOpen`, `slotPrefill` to CalendarioPage
- [x] 2.4 Add `toLocalISOString(date: Date): string` helper (returns `date.toISOString()`)
- [x] 2.5 Compute `const { user } = useAuth()` and `const isAdmin = user?.roles?.includes('admin') ?? false`

## Phase 3: CalendarioPage — EventoForm Modal Wiring

- [x] 3.1 Replace `"+ Nuevo Evento"` button `onClick` toast with: `setEditingEvent(null); setSlotPrefill(null); setIsEventoFormOpen(true)`
- [x] 3.2 Add `onSelectSlot` handler to Calendar: compute `slotPrefill` from slot start/end, set `isEventoFormOpen(true)`
- [x] 3.3 In the detail modal, replace "Editar" button toast with: `setEditingEvent(selectedEvent?.resource ?? null); setSelectedEvent(null); setIsEventoFormOpen(true)`
- [x] 3.4 Add `onSuccess` callback to CalendarioPage that calls `fetchData()` to refresh after mutations
- [x] 3.5 Render `<EventoForm>` component: pass `isOpen={isEventoFormOpen}`, `onClose`, `event={editingEvent}`, `onSuccess={fetchData}`, and `initialDates` from `slotPrefill` (convert Dates to ISO strings via `toLocalISOString`)
- [x] 3.6 Verify: `tsc --noEmit` passes

## Phase 4: CalendarioPage — Drag & Drop

- [x] 4.1 Conditionally wrap Calendar: `const DnDCalendar = isAdmin ? withDragAndDrop(Calendar) : Calendar`
- [x] 4.2 Replace `<Calendar ...>` in JSX with `<DnDCalendar ...>` using the same props
- [x] 4.3 Add `onEventDrop` handler: extract `{start, end, event}`, call `updateEvento(event.resource.id, {fecha_inicio: toLocalISOString(start), fecha_fin: toLocalISOString(end)})`, then `fetchData()`. Wrap in try/catch with `toast.error`
- [x] 4.4 Add `onEventResize` handler: same logic as `onEventDrop`
- [x] 4.5 Add `resizable={isAdmin}` prop to calendar (recepcion cannot resize)
- [x] 4.6 Verify: `tsc --noEmit` passes

## Phase 5: CalendarioPage — Delete Gating

- [x] 5.1 In the detail modal actions, wrap the "Eliminar" button in `{isAdmin && (...)}` conditional render
- [x] 5.2 Replace "Eliminar" button `onClick` toast with: `window.confirm('¿Eliminar este evento?') && deleteEvento(selectedEvent.resource.id).then(() => { toast.success('Evento eliminado correctamente'); setSelectedEvent(null); fetchData(); }).catch(err => toast.error(err instanceof Error ? err.message : 'Error al eliminar'))`
- [x] 5.3 Verify: `tsc --noEmit` passes

## Phase 6: CalendarioPage — TipoEventoAdmin Button

- [x] 6.1 Add "Gestionar Tipos" button in header section, visible only when `isAdmin` (conditional render)
- [x] 6.2 Button `onClick` sets `setIsTipoAdminOpen(true)`
- [x] 6.3 Render `<TipoEventoAdmin>` inside a modal wrapper (conditional on `isTipoAdminOpen`) with close button calling `setIsTipoAdminOpen(false)`; pass `onSuccess={fetchData}` so tipo changes refresh calendar types
- [x] 6.4 Verify: `tsc --noEmit` passes

## Phase 7: SideBarUser — Dead Link Fix

- [x] 7.1 In `SideBarUser.tsx` line 76, change `to='#'` to `to='/dashboard/calendar'` for the Calendario `SidebarItem`
- [x] 7.2 Verify: `tsc --noEmit` passes

## Phase 8: Final Verification

- [x] 8.1 Run `tsc --noEmit` from `gimnasioReact/` — expect zero errors
- [x] 8.2 Run `npm run build` from `gimnasioReact/` — expect successful build
- [x] 8.3 QA Manual Checklist:
  - Admin: click "+ Nuevo Evento" → EventoForm opens create mode → submit → event appears
  - Admin: click event → detail modal → "Editar" → EventoForm edit mode → submit → event updated
  - Admin: click empty slot → EventoForm opens with prefilled dates
  - Admin: drag event → persisted on drop (verify API call)
  - Admin: resize event → persisted on resize
  - Admin: click event → detail modal → "Eliminar" → confirm → event deleted
  - Admin: "Gestionar Tipos" button visible → TipoEventoAdmin modal opens → CRUD works
  - Recepcion: "+ Nuevo Evento" visible → create works
  - Recepcion: no "Eliminar" button in detail modal
  - Recepcion: no "Gestionar Tipos" button
  - Recepcion: cannot drag events (no cursor feedback)
  - SideBar: Calendario link navigates to `/dashboard/calendar`