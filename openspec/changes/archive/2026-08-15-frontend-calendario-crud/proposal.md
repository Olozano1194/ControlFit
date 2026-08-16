# Proposal: Frontend Calendar CRUD (Nivel 1)

## Intent

Recepción and admin can only READ the calendar: create/edit/delete are toast placeholders, and recepción cannot even reach the page (`SideBarUser` Calendario link is `to='#'`). Backend (committed `da69a52`, 79 tests) and frontend contract + recovered components are complete but unwired. This change activates full event CRUD, TipoEvento management, and drag & drop.

## Scope

### In Scope
- Wire `EventoForm` modal into `CalendarioPage`: "+ Nuevo Evento" (create), detail-modal "Editar" (edit)
- `onSelectSlot`: click empty slot → create form with dates prefilled
- DnD via `withDragAndDrop(Calendar)` (RBC 1.20.0 addon, native HTML5, no react-dnd): `onEventDrop`/`onEventResize` persist via `updateEvento` + refetch
- Delete: `window.confirm` + `deleteEvento`; hide button for recepción (backend already 403s recepción DELETE — verified `permissions.py:26-30`, no backend change)
- TipoEvento: admin-only header button (gated via `useAuth().user?.roles`) opens `TipoEventoAdmin` modal (modal-only)
- Fix `SideBarUser` dead link `to='#'` → `/dashboard/calendar`

### Out of Scope
- Recurrence, public view, notifications, iCal export, reports (Nivel 2/3)
- Dedicated tipo page; overlap validation (explicitly NOT added)
- Backend permission changes; range-limited fetching (later)

## Capabilities

> `openspec/specs/` empty; backend delta specs in `openspec/changes/backend-calendario/specs/`. All New.

### New Capabilities
- `calendario-eventos-frontend`: event CRUD UX — modal create/edit, slot-click prefill, DnD persistence, admin-only delete, recepción read/write/no-delete
- `calendario-tipos-frontend`: admin-only modal TipoEvento management from the calendar screen

### Modified Capabilities
- None (no main specs exist)

## Approach

Reuse recovered components as designed (modal-only). `CalendarioPage` owns `EventoForm` + `TipoEventoAdmin` modal state; DnD handlers convert RBC local `Date` slots to ISO strings before `updateEvento`; role gating via `useAuth()`; refetch after each mutation.

## Affected Areas

| Path | Impact | Description |
|------|--------|-------------|
| `gimnasioReact/src/pages/admin/calendario/CalendarioPage.tsx` | Modified | Wire modals, DnD wrapper, slot prefill, delete gating, tipos button |
| `gimnasioReact/src/components/sideBar/SideBarUser.tsx` | Modified | Fix `to='#'` → `/dashboard/calendar` |
| `EventoForm/TipoEventoAdmin/Form/List.tsx` | Reused | Unchanged (tracked, compiles clean) |
| `gimnasioReact/package.json` | Unchanged | DnD built into RBC 1.20.0 |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| DnD datetime drift (local slots vs `toISOString` UTC) | Med | Single conversion helper; manual QA |
| Tipo delete SET_NULL nulls events silently; 409 branch dead | Low | Accept backend semantics; minor cleanup |
| No frontend test runner | High | `tsc`/`npm run build` + manual QA checklist |
| Recepción sees delete button → 403 | Low | Hide via role gate, not error handling |

## Rollback Plan

Revert the feature commit; components stay tracked dead code, no data risk (frontend-only).

## Dependencies

- Backend calendar endpoints live (committed); `react-big-calendar@^1.20.0` installed.

## Success Criteria

- [ ] Admin: full CRUD events + tipos via modals; DnD persists on drop/resize
- [ ] Recepción: create/edit events, cannot delete (no button, 403 if forced)
- [ ] Slot click opens prefilled create form
- [ ] Recepción sidebar link navigates to calendar
- [ ] `tsc --noEmit` + `npm run build` pass; manual QA sign-off