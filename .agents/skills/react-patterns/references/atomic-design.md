# Atomic Design Rules for ControlFit Frontend

## Layer Structure

```
src/components/
├── atoms/           # Indivisible UI elements
│   ├── Button/
│   ├── Input/
│   ├── Label/
│   ├── Icon/
│   ├── Badge/
│   ├── Avatar/
│   └── index.ts
├── molecules/       # Simple combinations of atoms
│   ├── FormField/          # Label + Input + Error
│   ├── ButtonGroup/        # Multiple buttons
│   ├── SearchInput/        # Input + Icon + Clear
│   ├── SelectField/        # Label + Select + Error
│   ├── DatePickerField/    # Label + DatePicker + Error
│   └── index.ts
├── organisms/       # Complex UI sections
│   ├── MembershipCard/
│   ├── PaymentForm/
│   ├── MemberTable/
│   ├── NotificationBell/
│   ├── Sidebar/
│   ├── Header/
│   └── index.ts
└── templates/       # Page-level layouts (optional)
    ├── DashboardLayout/
    ├── AuthLayout/
    └── index.ts
```

## Rules by Layer

### Atoms
- **Single responsibility**: one visual element
- **No business logic**: purely presentational
- **ForwardRef required**: for DOM access in parents
- **Props interface**: explicit, documented with JSDoc
- **CSS Modules**: scoped styles, BEM-like naming
- **No TanStack Query / RHF**: no server state, no form logic
- **Test**: snapshot + props variations

### Molecules
- **Compose atoms**: 2-5 atoms combined
- **Single interaction**: one user action (search, select, input group)
- **May have local state**: controlled/uncontrolled toggle
- **May use simple hooks**: `useId`, `useClickOutside`
- **No direct API calls**: receive data via props
- **Test**: interaction + accessibility

### Organisms
- **Business logic allowed**: hooks, queries, mutations
- **Compose molecules + atoms**: 3+ components
- **Connected to backend**: TanStack Query, RHF forms
- **Page sections**: sidebar, header, data tables, forms
- **Test**: integration (mock query/mutation)

### Templates (Pages)
- **Route-level**: correspond to routes in `routes/`
- **Compose organisms**: layout + data fetching
- **Handle loading/error/empty states**
- **No direct API**: use organisms that encapsulate queries

## Import Rules

```typescript
// ✅ Good: explicit layer imports
import { Button } from '@/components/atoms';
import { FormField } from '@/components/molecules';
import { MembershipCard } from '@/components/organisms';

// ❌ Bad: deep imports
import { Button } from '@/components/atoms/Button/Button';
```

## Naming Conventions

| Layer | Folder | Component | Export |
|-------|--------|-----------|--------|
| Atom | `Button/` | `Button.tsx` | `Button` |
| Molecule | `FormField/` | `FormField.tsx` | `FormField` |
| Organism | `MembershipCard/` | `MembershipCard.tsx` | `MembershipCard` |

Each component folder:
```
ComponentName/
├── ComponentName.tsx
├── ComponentName.module.css
├── ComponentName.test.tsx
└── index.ts  // re-exports ComponentName
```

## Composition Examples

```tsx
// Atom → Molecule
// atoms/Input + atoms/Label + atoms/ErrorMessage → molecules/FormField

// Molecule → Organism
// molecules/FormField + molecules/ButtonGroup + atoms/Alert → organisms/PaymentForm

// Organism → Template/Page
// organisms/Sidebar + organisms/Header + organisms/MemberTable → pages/Dashboard
```

## Anti-Patterns to Avoid

- ❌ Atom using `useQuery` or `useMutation`
- ❌ Molecule making direct `fetch` calls
- ❌ Organism importing another organism (compose via page/template)
- ❌ Skipping layers (atom → organism directly)
- ❌ Business logic in atoms/molecules
- ❌ Global CSS classes in components