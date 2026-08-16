# Apply Progress: Frontend Calendar CRUD (Nivel 1)

**Change**: frontend-calendario-crud
**Batch**: 1 (único) — all 33 tasks across 8 phases
**Date**: 2026-08-15
**Mode**: Standard (no test runner en frontend; verificación = `tsc` + `npm run build` + QA manual)
**Delivery**: single PR — 4 archivos modificados (~218 líneas autorales), bajo el presupuesto de 400. Chain strategy: size-exception (no aplica).

## Tasks Completed

**Phase 1 — EventoForm `initialDates` prop (1.1–1.4)** ✅
- `EventoFormProps` gana `initialDates?: { start: string; end: string }`; destructuring actualizado; el `useEffect` de reset usa `initialDates` (sliced a `YYYY-MM-DDTHH:mm`) cuando `event` es null y viene prefill; `initialDates` agregado a deps.

**Phase 2 — CalendarioPage imports/state/helpers (2.1–2.5)** ✅
- Imports: `withDragAndDrop` (default export del addon), `useAuth`, `updateEvento`/`deleteEvento`, `EventoForm`, `TipoEventoAdmin`, `styles.css` del addon.
- State: `isEventoFormOpen`, `editingEvent`, `isTipoAdminOpen`, `slotPrefill`.
- Helper `toLocalISOString(date) => date.toISOString()`; `isAdmin = user?.roles?.includes('admin') ?? false`.

**Phase 3 — Wiring de EventoForm (3.1–3.6)** ✅
- Botón "+ Nuevo Evento" abre el modal en create mode; `onSelectSlot` prefill desde slot clickeado; "Editar" abre edit mode con el recurso del evento; `onSuccess={handleEventFormSuccess}` → `fetchData()`; `<EventoForm>` con `initialDates` convertidos vía `toLocalISOString`.

**Phase 4 — Drag & Drop (4.1–4.6)** ✅
- `DnDCalendar` condicional (admin: `withDragAndDrop<CalendarEvent>(Calendar)`, recepción: `Calendar` plano), memoizado con `useMemo`; `onEventDrop`/`onEventResize` → `updateEvento(id, {fecha_inicio, fecha_fin})` → `fetchData()`, con try/catch + `toast.error`; `resizable={isAdmin}`.

**Phase 5 — Delete gating (5.1–5.3)** ✅
- "Eliminar" solo renderizado si `isAdmin`; `window.confirm('¿Eliminar este evento?')` → `deleteEvento` → success toast → cierra modal → `fetchData()`, catch con `toast.error`.

**Phase 6 — Botón Gestionar Tipos (6.1–6.4)** ✅
- Botón "Gestionar Tipos" admin-only en el header; abre modal overlay con `<TipoEventoAdmin onSuccess={fetchData} />` y botón de cierre.

**Phase 7 — SideBarUser (7.1–7.2)** ✅
- `to='#'` → `to='/dashboard/calendar'` para el item Calendario (ruta real verificada en App.tsx).

**Phase 8 — Verificación final (8.1–8.3)** ✅
- `tsc -b` exit 0 (ver detalle abajo); `npm run build` exit 0; checklist QA manual analizado estáticamente (ver sección QA).

## Verification Results

| Check | Command | Result |
|-------|---------|--------|
| Typecheck (real) | `npx tsc -b` desde `gimnasioReact/` | **exit 0, cero errores** |
| Build | `npm run build` desde `gimnasioReact/` | **exit 0** — 1291 módulos, built in 8.71s (warning de chunk >500 kB pre-existente, no relacionado) |

⚠️ **Nota de verificación**: `npx tsc --noEmit` sobre el tsconfig raíz es un **no-op** (tsconfig de solución con `files: []` y `references`). El chequeo real es `tsc -b`, que respeta `noEmit: true` de `tsconfig.app.json`. El fix de tipos del DnD addon se encontró precisamente porque `tsc -b` sí chequea los archivos.

## Work Unit Evidence

| Evidence | Value |
|----------|-------|
| Focused test command & result | `npx tsc -b` → exit 0, cero errores de tipo |
| Runtime harness & result | `npm run build` → exit 0 (vite build completo; 1291 módulos transformados) |
| Rollback boundary | Revertir los 4 archivos modificados (CalendarioPage, EventoForm, TipoEventoAdmin, SideBarUser) restaura el estado previo; los componentes recuperados ya eran código muerto trackeado, sin riesgo de datos |

## Deviations from Design / Tasks

1. **`createEvento` no importado en CalendarioPage** (task 2.1 lo listaba): vive en EventoForm; importarlo aquí dispararía `noUnusedLocals` (strict). Sin cambio funcional.
2. **`DragAndDropCalendarProps` no es exportable**: la interface en `@types/react-big-calendar/lib/addons/dragAndDrop.d.ts` es privada de módulo (sin `export`). El cast se resuelve con `ReturnType<typeof withDragAndDrop<CalendarEvent>>` (instantiation expression, TS 4.7+).
3. **`withDragAndDrop` es default export** del addon (no named): `import withDragAndDrop from '...'`.
4. **DnD wrapper memoizado con `useMemo`**: el diseño decía `const Cal = isAdmin ? withDragAndDrop(Calendar) : Calendar` plano — eso recrearía la identidad del componente en CADA render y remontaría todo el calendario. `useMemo([isAdmin])` mantiene la identidad estable. Misma intención, implementación corregida.
5. **`TipoEventoAdmin` ganó prop opcional `onSuccess?: () => void`**: el diseño decía "Reused | Unchanged", pero la task 6.3 exige pasar `onSuccess={fetchData}` y el spec exige refresh del calendario tras cambios de tipos. Cambio mínimo y retrocompatible (se invoca tras `fetchTipos()` en `handleSuccess`).
6. **Guard en delete**: `const eventId = selectedEvent.resource?.id; if (!eventId) return;` en vez de `selectedEvent.resource.id` pelado — `resource` es opcional en `CalendarEvent`, TS estricto lo exige.
7. **`handleEventResize = handleEventDrop`**: misma lógica compartida (task 4.4: "same logic as onEventDrop").
8. **Slot prefill en vista mes**: RBC entrega `start = 00:00 del día` y `end = 00:00 del día siguiente`; la spec decía 23:59. Se pasan los valores crudos del slot (task 3.2). Nuance menor.

## Risks / QA Notes

- **Zona horaria en prefill**: `toLocalISOString` produce UTC; el campo `datetime-local` mostrará la hora UTC (no local) para usuarios fuera de UTC. Consistente con el comportamiento existente del edit mode (que slicea el ISO del backend) y con la decisión de diseño del helper único. **Requerido QA en zona no-UTC** (ej. Argentina UTC-3).
- **ESLint del entorno roto** (pre-existente): `node_modules/@eslint/eslintrc/node_modules/globals/globals.json` está corrupto ("p/commit/b..." no es JSON). No es parte del contrato de verificación (tsc + build). `npm run lint` no es ejecutable en este entorno.
- **QA manual pendiente** (fase 8.3): los flujos runtime (crear/editar/eliminar evento, DnD persistido, CRUD de tipos, role gating visual) requieren usuario real. Verificación estática: todos los gate `isAdmin`, handlers, toasts y confirms están cableados según spec.

## QA Manual Checklist — Static Status

| Item | Verificación estática |
|------|----------------------|
| Admin "+ Nuevo Evento" → create mode → submit → evento aparece | Cableado: onClick → modal; submit → createEvento → onSuccess → fetchData. Runtime: QA manual |
| Admin Editar → edit mode → submit → update | Cableado: resource → editingEvent → updateEvento. Runtime: QA manual |
| Admin click slot vacío → prefill | Cableado: onSelectSlot → slotPrefill → initialDates. Runtime: QA manual (+ nota TZ) |
| Admin drag → persistido | Cableado: onEventDrop → updateEvento → fetchData. Runtime: QA manual |
| Admin resize → persistido | Cableado: onEventResize (misma fn) + resizable. Runtime: QA manual |
| Admin Eliminar → confirm → borrado | Cableado: isAdmin && window.confirm → deleteEvento. Runtime: QA manual |
| Admin "Gestionar Tipos" → modal → CRUD | Cableado: isAdmin && modal + onSuccess. Runtime: QA manual |
| Recepción "+ Nuevo Evento" visible | "+ Nuevo Evento" NO está gateado por rol ✓ (estático) |
| Recepción sin botón Eliminar | `{isAdmin && ...}` ✓ (estático) |
| Recepción sin botón Gestionar Tipos | `{isAdmin && ...}` ✓ (estático) |
| Recepción no puede arrastrar | DnDCalendar = Calendar plano (sin wrapper) cuando !isAdmin ✓ (estático + código) |
| SideBar Calendario → /dashboard/calendar | `to='/dashboard/calendar'` y ruta existe en App.tsx ✓ (estático) |