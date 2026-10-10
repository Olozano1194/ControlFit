---
name: react-patterns
description: "Trigger: React component, hook, form, query, TypeScript, atomic design, Vitest, RTL. Production-grade React/TypeScript patterns for ControlFit frontend."
license: Apache-2.0
metadata:
  author: "oscar-personal"
  version: "1.0"
---

# React/TypeScript Patterns for ControlFit

## Activation Contract

Load this skill when working on `gimnasioReact/src/` for:
- Creating components (atomic design: atoms → molecules → organisms)
- Writing custom hooks (data fetching, mutations, form logic)
- Building forms with React Hook Form + Zod validation
- Using TanStack Query for server state (queries, mutations, invalidation)
- Writing tests with Vitest + React Testing Library
- TypeScript patterns (strict mode, discriminated unions, branded types)

## Hard Rules

- **Strict TypeScript**: `strict: true`, `noUncheckedIndexedAccess: true`, `exactOptionalPropertyTypes: true`
- **Atomic design enforced**: atoms in `components/atoms/`, molecules in `components/molecules/`, organisms in `components/organisms/`, pages in `pages/`
- **React Hook Form + Zod**: all forms use `useForm` with `zodResolver`, schema in `schemas/`
- **TanStack Query**: all server state via `useQuery`/`useMutation`, keys in `queryKeys.ts`, invalidate on mutation
- **No `any`**: use `unknown`, branded types, or discriminated unions
- **CSS Modules**: scoped styles in `*.module.css`, no global CSS except `index.css`
- **Path aliases**: `@/` = `src/`, `@components/` = `src/components/`, `@hooks/` = `src/hooks/`

## Decision Gates

| Situation | Choice |
|-----------|--------|
| New UI element | Atom → Molecule → Organism (compose up) |
| Form with validation | RHF + Zod schema in `schemas/` |
| Server data read | `useQuery` with key from `queryKeys.ts` |
| Server data write | `useMutation` + `invalidateQueries` |
| Complex client state | Custom hook in `hooks/` |
| Test needed | Vitest + RTL, colocated `*.test.tsx` |

## Execution Steps

1. **Identify layer**: atom / molecule / organism / page / hook / schema / query
2. **Check existing patterns** in same layer (reuse before create)
3. **Create TypeScript types first** (discriminated unions for variants, branded IDs)
4. **Implement component/hook** with minimal props, forwardRef for atoms
5. **Add Zod schema** if form input involved
6. **Add TanStack Query key** if server state involved
7. **Write test** (happy path + error + edge case) in colocated `*.test.tsx`
8. **Export from layer index** (`components/atoms/index.ts`, etc.)

## Output Contract

Return created/modified files with:
- Component: `Component.tsx`, `Component.module.css`, `Component.test.tsx`, export in layer `index.ts`
- Hook: `useHook.ts`, `useHook.test.ts`
- Schema: `schema.ts` in `schemas/`
- Query keys: update `queryKeys.ts`

## References

- `assets/component-template.tsx` — base component structure
- `assets/hook-template.ts` — custom hook template
- `assets/form-schema-template.ts` — RHF + Zod schema template
- `assets/query-key-template.ts` — TanStack Query key factory
- `references/atomic-design.md` — atomic design rules for this project
- `references/testing-patterns.md` — Vitest + RTL patterns