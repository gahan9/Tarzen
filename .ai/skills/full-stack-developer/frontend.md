# Frontend Playbook

Reference for the UI layer. Load when building or reviewing client-side code.
Defaults: React + TypeScript. Principles transfer to Vue/Svelte/Angular.

## Foundations first

Frameworks do not excuse weak fundamentals. Get these right regardless of stack:

- **Semantic HTML** — use the right element (`<button>`, `<nav>`, `<main>`,
  `<label>`). Div-soup is an accessibility and SEO bug.
- **CSS layout** — Flexbox for 1D, Grid for 2D. Mobile-first responsive design
  with relative units; design tokens (CSS variables) over magic numbers.
- **Modern JavaScript** — closures, `async`/`await`, modules, immutability,
  array methods. Understand the event loop and the `fetch`/Promise model before
  reaching for a library.

## Component design

- **Single responsibility.** A component renders one thing or coordinates a few.
  If it does data fetching, formatting, and layout, split it.
- **Props down, events up.** Keep components pure where possible; push side
  effects to the edges (hooks, loaders).
- **Composition over configuration.** Prefer `children`/slots and small composable
  components to a 20-prop mega-component.
- **Type the props.** No untyped/`any` boundaries.

```tsx
type UserCardProps = {
  user: User;
  onSelect: (id: string) => void;
};

export function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <button type="button" onClick={() => onSelect(user.id)}>
      {user.name}
    </button>
  );
}
```

## State management — escalate, don't over-reach

Choose the *smallest* tool that fits. Most "we need Redux" instincts are wrong.

| Scope | Use |
|-------|-----|
| One component | local state (`useState`/`useReducer`) |
| A subtree | lift state up, or Context (low-frequency values) |
| Server data (most app state) | a data-fetching cache: TanStack Query / RTK Query / SWR |
| Genuinely global client state | Zustand / Redux Toolkit / Jotai |

Key insight: **most "global state" is really server state.** A query cache
(TanStack Query) handles fetching, caching, dedup, and refetch — reaching for a
global store to hold server data is a common anti-pattern.

## Hooks discipline (React)

- Effects are for synchronizing with external systems, not for deriving values —
  compute derived data during render.
- Every effect declares complete dependencies; clean up subscriptions/timers.
- Extract reusable logic into custom hooks (`useDebounce`, `useUser`).
- `useMemo`/`useCallback` are for measured problems (referential stability,
  expensive compute), not reflexive wrapping.

## Forms & validation

- Use a form library for non-trivial forms (React Hook Form / Formik).
- Validate with a schema (Zod/Yup) and **share the schema with the server** when
  possible — single source of truth.
- Client validation is for UX; the server still re-validates. Never trust client
  input as authoritative.

## Data fetching

- Handle all four states: loading, success, empty, error. Empty ≠ error.
- Show optimistic UI only when you can roll back on failure.
- Cancel/ignore stale requests (race conditions on fast typing/navigation).
- Never put secrets or privileged logic in the client — it is fully visible.

## Performance

Measure with the browser profiler / Lighthouse before optimizing.

- **Code-split** by route and lazy-load heavy components (`React.lazy`, dynamic
  import).
- **Virtualize** long lists (react-window/virtual).
- Optimize images (right format/size, lazy `loading`, responsive `srcset`).
- Avoid unnecessary re-renders: stable keys, memo at proven hot spots, colocate
  state to limit render scope.
- Watch bundle size; analyze and prune dependencies.
- Core Web Vitals (LCP, CLS, INP) are the user-facing scoreboard.

## Accessibility (a correctness requirement)

- Semantic elements; ARIA only to fill gaps, never to replace native semantics.
- Every input has a `<label>`; interactive elements are keyboard reachable and
  have visible focus.
- Sufficient color contrast; don't encode meaning in color alone.
- Test with keyboard-only navigation and a screen reader on critical flows.

## TypeScript hygiene

- `strict` on. No `any` at module boundaries; prefer `unknown` + narrowing.
- Model domain types once and share them with the backend (generated types or a
  shared package) so the API contract can't silently drift.

## Review checklist

- [ ] Semantic, accessible markup; labels and keyboard support
- [ ] Components small and single-purpose; props typed
- [ ] State at the right scope; server state in a query cache, not a global store
- [ ] Loading / empty / error states all handled
- [ ] No secrets or privileged logic in the client
- [ ] No obvious re-render or bundle-size problems
- [ ] Inputs validated (schema), errors surfaced to the user
