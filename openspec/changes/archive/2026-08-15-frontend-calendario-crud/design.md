# Design: Frontend Calendar CRUD (Nivel 1)

## Technical Approach

Wire recovered components (EventoForm, TipoEventoAdmin) into CalendarioPage using modal-only architecture. Implement DnD via react-big-calendar's native addon (no react-dnd dependency). Apply role gating via useAuth() for admin-only operations (delete, tipo management). Single datetime conversion helper ensures UTC consistency between RBC local slots and API ISO strings.

## Architecture Decisions

### Decision: Modal-Only vs Page-Based Tipo Management

**Choice**: Modal-only (Approach 1 from exploration)
**Alternatives considered**: Page-based tipo management with dedicated route, Hybrid-lite
**Rationale**: 
- Minimal diff: CalendarioPage already has placeholder toasts; wiring modals is ~150-250 lines
- Components already built for modal UX (EventoForm, TipoEventoAdmin)
- No routing/sidebar changes needed; single-screen UX
- Tradeoff: cramped for many tipos, but acceptable for Nivel 1; can upgrade to page later without rework

### Decision: DnD via Native Addon (No react-dnd)

**Choice**: `withDragAndDrop(Calendar)` from react-big-calendar/lib/addons/dragAndDrop
**Alternatives considered**: react-dnd with custom backend, manual drag implementation
**Rationale**:
- DnD addon is self-contained: native HTML5 DnD, zero external deps
- Already installed with react-big-calendar@1.20.0; no package.json changes
- Addon API matches needs: onEventDrop({start,end,event}), onEventResize, resizable flag
- Tradeoff: less control than react-dnd, but sufficient for move/resize operations

### Decision: Role Gating via useAuth() Client-Side

**Choice**: Client-side role checks using useAuth().user?.roles
**Alternatives considered**: Server-side only (backend already 403s recepcion DELETE)
**Rationale**:
- UX: hide delete button for recepcion (not just error on 403)
- Consistent with existing pattern (SideBarAdmin vs SideBarUser)
- Backend provides defense-in-depth (permissions.py:26-30 blocks DELETE)
- Tradeoff: client-side can be bypassed, but acceptable for internal app

### Decision: Conditional DnD Wrapper for Role Gating

**Choice**: Conditionally wrap Calendar with `withDragAndDrop` only when user is admin
**Alternatives considered**: Always wrap but disable handlers, use `resizable={false}`
**Rationale**:
- Spec requires recepcion cannot drag ("drag operation is not initiated")
- Conditionally wrapping: `const Cal = isAdmin ? withDragAndDrop(Calendar) : Calendar`
- Alternative (always wrap, no handlers) still shows drag cursor/feedback — violates spec
- Clean separation: admin gets DnD, recepcion gets static calendar

### Decision: Single Datetime Conversion Helper

**Choice**: `toLocalISOString(date: Date): string` helper function
**Alternatives considered**: Inline conversion, moment.js, date-fns-tz
**Rationale**:
- RBC slots are local Date objects; API expects ISO UTC strings
- Helper ensures consistent conversion: `date.toISOString()` (UTC)
- Prevents timezone drift in DnD operations
- Single point of truth for datetime handling

## Data Flow

### Event Creation Flow
```
"+ Nuevo Evento" button → Open EventoForm (create mode)
onSelectSlot → Open EventoForm (create mode, prefilled dates)
EventoForm submit → createEvento(dto) → refetch events → close modal
```

### Event Editing Flow
```
Event click → Open detail modal → Click "Editar" → Open EventoForm (edit mode, prefilled)
EventoForm submit → updateEvento(id, dto) → refetch events → close modal
```

### Event Deletion Flow (Admin Only)
```
Event click → Open detail modal → Click "Eliminar" → window.confirm
If confirmed → deleteEvento(id) → refetch events → close modal
Recepcion: delete button hidden via role gate
```

### DnD Flow
```
Drag event → onEventDrop({start, end, event}) → toLocalISOString(start/end)
→ updateEvento(event.id, {fecha_inicio, fecha_fin}) → refetch events
Resize event → onEventResize({start, end, event}) → same flow
```

### TipoEvento Management Flow (Admin Only)
```
"Gestionar Tipos" button (admin-only) → Open TipoEventoAdmin modal
TipoEventoAdmin → TipoEventoList (table with edit/delete)
Edit → TipoEventoForm (edit mode) → updateTipoEvento → refetch tipos
Create → TipoEventoForm (create mode) → createTipoEvento → refetch tipos
Delete → window.confirm → deleteTipoEvento → refetch tipos (409 handled)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `gimnasioReact/src/pages/admin/calendario/CalendarioPage.tsx` | Modify | Wire EventoForm + TipoEventoAdmin modals, DnD wrapper, slot prefill, delete gating, tipos button |
| `gimnasioReact/src/components/sideBar/SideBarUser.tsx` | Modify | Fix `to='#'` → `/dashboard/calendar` for Calendario link |
| `gimnasioReact/src/pages/admin/calendario/EventoForm.tsx` | Modify (minor) | Add optional `initialDates?: {start: string; end: string}` prop for slot-click prefill; integrate into existing useEffect reset logic |
| `gimnasioReact/src/pages/admin/calendario/EventoForm.tsx` | Modify (minor) | Also needs `onSelectSlot`-driven date prefill when `initialDates` provided but `event` is null |
| `gimnasioReact/src/pages/admin/calendario/TipoEventoAdmin.tsx` | Reused | Unchanged (container, renders TipoEventoList + TipoEventoForm) |
| `gimnasioReact/src/pages/admin/calendario/TipoEventoForm.tsx` | Reused | Unchanged (modal, color picker, validation) |
| `gimnasioReact/src/pages/admin/calendario/TipoEventoList.tsx` | Reused | Unchanged (table with edit/delete, 409 handling dead branch) |

## Interfaces / Contracts

### CalendarioPage State Interface
```typescript
interface CalendarioPageState {
  eventos: EventoCalendario[];
  tipos: TipoEvento[];
  isLoading: boolean;
  selectedEvent: CalendarEvent | null;  // detail modal
  isEventoFormOpen: boolean;
  editingEvent: EventoCalendario | null;  // null = create mode
  isTipoAdminOpen: boolean;
  slotPrefill: { start: Date; end: Date } | null;  // from onSelectSlot
}
```

### EventoForm Props Contract (EXTENDED — needs `initialDates` prop)
```typescript
interface EventoFormProps {
  isOpen: boolean;
  onClose: () => void;
  event?: EventoCalendario | null;  // null = create mode, defined = edit mode
  onSuccess: () => void;  // refetch callback
  initialDates?: { start: string; end: string };  // NEW: prefill from slot click
}
// Current component only has isOpen/onClose/event/onSuccess.
// initialDates integration: in the existing useEffect reset, when event is null
// and initialDates is provided, set fecha_inicio/fecha_fin from initialDates.
```

### DnD Handler Contract
```typescript
// Input: RBC provides local Date objects
interface DnDInfo {
  start: Date;  // local timezone
  end: Date;    // local timezone
  event: CalendarEvent;  // contains resource: EventoCalendario
}

// Output: ISO strings for API
interface UpdateEventoPayload {
  fecha_inicio: string;  // ISO UTC
  fecha_fin: string;     // ISO UTC
}
```

### Datetime Conversion Helper
```typescript
// Converts local Date to ISO string (UTC) for API
// Used by: EventoForm submit, DnD handlers
const toLocalISOString = (date: Date): string => {
  return date.toISOString();  // UTC, matches backend DateTimeField
};

// Converts ISO string to local Date for display
// Used by: calendarEvents mapping
const fromISOString = (iso: string): Date => {
  return new Date(iso);  // JS parses ISO to local timezone
};
```

### Role Gating Helper
```typescript
// Check if user is admin
const isAdmin = (user: AuthUser | null): boolean => {
  return user?.roles?.includes('admin') ?? false;
};

// Used in CalendarioPage:
const { user } = useAuth();
const showDeleteButton = isAdmin(user);
const showTiposButton = isAdmin(user);
const enableDnD = isAdmin(user);  // recepcion cannot drag
```

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Datetime conversion helper | Manual test with timezone scenarios |
| Unit | Role gating logic | Verify isAdmin returns correct values |
| Integration | Event CRUD flows | Manual QA: create, edit, delete events |
| Integration | DnD persistence | Manual QA: drag/resize events, verify API calls |
| Integration | TipoEvento management | Manual QA: create/edit/delete types |
| E2E | Full calendar workflow | Manual QA checklist: slot click, modal flows, role gating |
| Build | TypeScript compilation | `tsc --noEmit` + `npm run build` |

## Threat Matrix

N/A — no routing, shell, subprocess, VCS/PR automation, executable-file classification, or process-integration boundary.

## Migration / Rollout

No migration required. Frontend-only change; backend already live with 79 tests green.

**Rollback**: Revert feature commit; components stay tracked dead code, no data risk.

## Risks & Mitigations

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| DnD datetime drift (local slots vs ISO UTC) | Med | Single conversion helper `toLocalISOString`; manual QA across timezones |
| Tipo delete SET_NULL nulls events silently | Low | Accept backend semantics; 409 branch dead code (minor cleanup or ignore) |
| No frontend test runner | High | `tsc`/`npm run build` + manual QA checklist |
| Recepcion sees delete button → 403 | Low | Hide via role gate (`isAdmin` check), not error handling |
| CalendarioPage complexity (busy with modals) | Med | Keep modals self-contained; defer page-based upgrade to Nivel 2 |
| Full-range fetch loads all events | Low | Acceptable for Nivel 1; optimize with `onNavigate`/`onView` later |

## Open Questions

- [ ] Should TipoEventoAdmin be a separate page later (Nivel 2) or stay modal-only?
- [ ] Is the dead 409 branch in TipoEventoList acceptable or should it be cleaned up?
- [ ] Should DnD be enabled for recepcion users (currently disabled per spec)?
