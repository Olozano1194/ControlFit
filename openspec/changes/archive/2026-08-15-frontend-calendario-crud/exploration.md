# Exploration: frontend-calendario-crud

Nivel 1: Full event CRUD, TipoEvento management, and drag & drop in the calendar module frontend.

## Current State

**Backend (done, committed `da69a52`, 79 tests green):**
- `TipoEventoViewSet` — `IsAdminUser` only (`gimnasioApp/views.py:839`).
- `EventoCalendarioViewSet` — `IsRecepcionUser` (admin + recepcion); recepcion CANNOT DELETE (`permissions.py:26-30`, `has_object_permission` blocks DELETE). Overlap range filter `?start=&end=`, `tipo` nested via `select_related`, `created_by` auto-set.
- `PublicCalendarioView` — `AllowAny`, not under `/gym/api/v1`.
- URLs match frontend contract exactly: `/TiposEvento/`, `/CalendarioEventos/`, `/api/calendario/publico/{id}/`.
- `EventoCalendario.tipo` FK uses `on_delete=SET_NULL` — deleting a tipo silently nulls events, NO 409 is ever returned.

**Frontend contract (complete, unmodified):**
- `src/model/calendario.model.ts` — `TipoEvento`, `TipoEventoSimple`, `Create/UpdateTipoEventoDto`, `EventoCalendario`, `Create/UpdateEventoDto`.
- `src/api/action/calendario.api.ts` — full CRUD client: `getTiposEvento`, `create/update/deleteTipoEvento`, `getEventos(start,end)`, `getEvento`, `create/update/deleteEvento`, `getEventosPublicos`. Uses `axiosPrivate` (JWT refresh queue, `withCredentials`).

**CalendarioPage.tsx (254 lines, current behavior):**
- RBC `Calendar` (month/week/day/agenda), `selectable` set but NO `onSelectSlot` handler.
- `eventPropGetter` colors events by `tipo_detalle.color`; detail modal shows tipo, description, dates.
- "+ Nuevo Evento", "Editar", "Eliminar" are all toast placeholders (comment: "PR 3: Abrir EventoForm").
- `_tipos` state loaded but unused. `fetchData` loads ALL events (no `?start=&end=` range).

**Recovered but UNWIRED (tracked in git, dead code, TypeScript compiles clean — `tsc --noEmit` exit 0):**
- `EventoForm.tsx` — modal (isOpen/onClose props), react-hook-form, create/edit via `createEvento`/`updateEvento`, datetime-local inputs, tipo select, relacion fields, fin>=inicio validation.
- `TipoEventoAdmin.tsx` — container: fetches tipos, renders `TipoEventoList` + `TipoEventoForm` modal.
- `TipoEventoForm.tsx` — modal, react-hook-form, color picker + preview, name validation.
- `TipoEventoList.tsx` — tanstack `Table` (sorting + pagination), edit/delete with `window.confirm`; expects 409 on delete (dead branch — backend uses SET_NULL).

**Navigation & roles:**
- Route: `dashboard/calendar` → `CalendarioPage` (`App.tsx:63`). No route for tipo management.
- `SideBarAdmin.tsx:78` — Calendario item → `/dashboard/calendar` (works). `SideBarUser.tsx:74-78` — Calendario item → `to='#'` (DEAD LINK for recepcion).
- Role gating pattern: `useAuth()` → `user.roles: UserRole[]` (`'admin' | 'recepcion'`); sidebar filters via `getSidebarMenusByRole`.

**Drag & drop (KEY FINDING):**
- Installed: `react-big-calendar@1.20.0` (package.json `^1.20.0`).
- The `dragAndDrop` addon (`react-big-calendar/lib/addons/dragAndDrop`) is SELF-CONTAINED: own `DnDContext` + `EventWrapper` (native HTML5 DnD). **Zero `react-dnd`/`react-dnd-html5-backend` imports** across the entire package — those deps are NOT installed and NOT needed.
- Addon API (`withDragAndDrop.js`): wraps Calendar, exposes `onEventDrop({start,end,event})`, `onEventResize`, `draggableAccessor`, `resizableAccessor`, `onDragOver`, `resizable` flag. `EventWrapper` reads accessors via `accessor(event, prop)`.

## Affected Areas

| Path | Impact |
|------|--------|
| `gimnasioReact/src/pages/admin/calendario/CalendarioPage.tsx` | Wire EventoForm (create/edit), delete w/ confirm, DnD calendar wrapper, tipo management entry, admin gating |
| `gimnasioReact/src/pages/admin/calendario/EventoForm.tsx` | Reused as-is (modal); optional slot prefill |
| `gimnasioReact/src/pages/admin/calendario/TipoEventoAdmin.tsx` (+List/Form) | Reused as-is; either embedded modal in CalendarioPage or new route |
| `gimnasioReact/src/App.tsx` + sidebar components | Only if page-based tipo route is chosen |
| `gimnasioReact/package.json` | NO change for DnD (built into RBC 1.20.0) |
| `gimnasioReact/src/components/sideBar/SideBarUser.tsx` | Fix `to='#'` → `/dashboard/calendar` (optional, recepcion access) |

## Approaches

1. **Modal-only (reuse recovered components as designed)** — Events via `EventoForm` modal (open from "+ Nuevo Evento", `onSelectSlot` prefill, and detail-modal "Editar"); delete via `window.confirm` + `deleteEvento` + refetch; "Tipos" button (admin-only) in header opens `TipoEventoAdmin` in a modal; DnD via `withDragAndDrop`.
   - Pros: Minimal diff; components already built for exactly this; one-screen UX; no routing/sidebar changes.
   - Cons: CalendarioPage gets busy; no deep-linkable tipo page; list-in-modal is cramped for many tipos.
   - Effort: Low-Medium.

2. **Page-based tipo management (project convention) + modal events** — New route `dashboard/tipos-evento` (or similar) rendering `TipoEventoAdmin` with breadcrumbs; sidebar item gated `roles: ['admin']` (matches "Usuario"/"Membresía" menus); events stay modal.
   - Pros: Matches dominant admin pattern (`ListMemberShips`, `ListUser`); roomier; deep-linkable; natural role gating.
   - Cons: New route + sidebar menu entry + App.tsx; two navigation patterns inside one module; larger diff.
   - Effort: Medium.

3. **Hybrid-lite** — Modal events + `TipoEventoAdmin` embedded as a modal in CalendarioPage now; defer dedicated tipo page to a later iteration.
   - Pros: Unblocks Nivel 1 with smallest surface; upgrades to page later without rework.
   - Cons: Same cramped-modal caveat as (1) temporarily.
   - Effort: Low-Medium.

## Recommendation

**Approach 1 (modal-only), aligned with the recovered code's original intent** (comment "PR 3: Abrir EventoForm"):
- Wire `EventoForm` into CalendarioPage: "+ Nuevo Evento" (create), detail-modal "Editar" (edit with `resource`), optional `onSelectSlot` prefill for quick create.
- Delete: `window.confirm` + `deleteEvento(event.id)` + `fetchData()`; **hide delete button for recepcion** (backend 403s it).
- Tipos: admin-only "Tipos de Evento" button in the header (gated via `useAuth().user?.roles?.includes('admin')`) opening `TipoEventoAdmin` as a modal overlay.
- DnD: `import withDragAndDrop from 'react-big-calendar/lib/addons/dragAndDrop'` → `const DnDCalendar = withDragAndDrop(Calendar)`; add `resizable`, `onEventDrop`, `onEventResize` handlers that call `updateEvento` with `fecha_inicio`/`fecha_fin` converted to ISO (UTC), then refetch. No dependency changes.
- Fix `SideBarUser` calendar link (`to='#'` → `/dashboard/calendar`) since recepcion is a first-class calendar user.
- If the user prefers a dedicated tipo page, Approach 2 is a clean escalation with the same components.

## Risks

- **Timezone/datetime conversion on DnD**: RBC slot dates are local `Date`; `EventoForm` submits `toISOString()` (UTC). Handlers must convert consistently or events shift hours. Backend stores DateTimeField.
- **recepcion delete UX**: backend blocks DELETE (403); frontend must hide the button, not rely on error handling alone.
- **Tipo delete semantics**: `SET_NULL` means deleting a tipo nulls its events silently; the `409` branch in `TipoEventoList` is dead code — minor cleanup or accept as-is.
- **No frontend test runner**: verification limited to `tsc`/`npm run build` + manual QA; strict_tdd does not apply to frontend.
- **Full-range fetch**: `getEventos()` without `?start=&end=` loads all events; acceptable for Nivel 1, optimize with `onNavigate`/`onView` later.
- **Line budget**: wiring is small (~150-250 lines) — no chain needed.

## Ready for Proposal

Yes. Proposal should cover: modal wiring, tipo management placement (modal vs page — recommend modal, confirm with user), DnD behavior (drag = move, resize = duration change, both persist via updateEvento), recepcion restrictions (no delete, no tipo management), and optional SideBarUser link fix.