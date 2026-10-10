# Vitest + React Testing Library Patterns for ControlFit

## Test File Structure

```
src/components/atoms/Button/
├── Button.tsx
├── Button.module.css
├── Button.test.tsx      # ← colocated
└── index.ts
```

## Test Categories

### 1. Unit Tests (Atoms / Hooks / Utils)
- Pure functions, no React rendering
- Custom hooks with `renderHook`
- Utility functions

### 2. Component Tests (Atoms / Molecules)
- Render with props
- User interactions (fireEvent, userEvent)
- Accessibility (role, aria-*)
- Snapshot (optional)

### 3. Integration Tests (Organisms / Pages)
- Mock TanStack Query (`@tanstack/react-query` provider)
- Mock React Hook Form
- Mock API calls (MSW or mocked fetch)
- Full user flows

## Setup (vitest.setup.ts)

```typescript
import '@testing-library/jest-dom';
import { vi } from 'vitest';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement } from 'react';

// Test QueryClient with no retries, no cache
const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0 },
      mutations: { retry: false },
    },
  });

// Wrapper with providers
const AllProviders = ({ children }: { children: React.ReactNode }) => {
  const [queryClient] = useState(() => createTestQueryClient());
  return (
    <QueryClientProvider client={queryClient}>
      {children}
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

export * from '@testing-library/react';
export { customRender as render, createTestQueryClient };
```

## Patterns by Layer

### Atoms — Snapshot + Props + Interaction

```tsx
// Button.test.tsx
import { render, screen } from '@/test-utils'; // custom render
import userEvent from '@testing-library/user-event';
import { Button } from './Button';

describe('Button', () => {
  it('renders with children', () => {
    render(<Button>Click me</Button>);
    expect(screen.getByRole('button', { name: 'Click me' })).toBeInTheDocument();
  });

  it('applies variant classes', () => {
    render(<Button variant="primary">Primary</Button>);
    expect(screen.getByRole('button')).toHaveClass('button--primary');
  });

  it('calls onClick when clicked', async () => {
    const handleClick = vi.fn();
    render(<Button onClick={handleClick}>Click</Button>);
    await userEvent.click(screen.getByRole('button'));
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('is disabled when loading', () => {
    render(<Button loading>Loading</Button>);
    expect(screen.getByRole('button')).toBeDisabled();
  });

  it('forwards ref', () => {
    const ref = vi.fn();
    render(<Button ref={ref}>Ref</Button>);
    expect(ref).toHaveBeenCalledWith(expect.any(HTMLButtonElement));
  });
});
```

### Molecules — Form Interaction + Validation

```tsx
// FormField.test.tsx
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { FormField } from './FormField';

describe('FormField', () => {
  it('shows error when touched and invalid', async () => {
    render(
      <FormField
        label="Email"
        name="email"
        error={true}
        helperText="Email inválido"
      >
        <input type="email" />
      </FormField>
    );
    
    const input = screen.getByLabelText('Email');
    await userEvent.click(input);
    await userEvent.tab(); // blur
    
    expect(screen.getByText('Email inválido')).toBeInTheDocument();
    expect(input).toHaveAttribute('aria-invalid', 'true');
  });

  it('clears error on change', async () => {
    render(<FormField name="email" error helperText="Error"><input /></FormField>);
    const input = screen.getByLabelText('Email');
    await userEvent.type(input, 'a');
    expect(screen.queryByText('Error')).not.toBeInTheDocument();
  });
});
```

### Custom Hooks — renderHook

```tsx
// useFeatureName.test.ts
import { renderHook, act } from '@testing-library/react';
import { useFeatureName } from './useFeatureName';

describe('useFeatureName', () => {
  it('returns initial state', () => {
    const { result } = renderHook(() => useFeatureName());
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('sets loading during action', async () => {
    const { result } = renderHook(() => useFeatureName());
    await act(async () => {
      await result.current.doSomething('test');
    });
    expect(result.current.isLoading).toBe(false);
  });

  it('captures error', async () => {
    const { result } = renderHook(() => useFeatureName());
    // Mock failure
    await act(async () => {
      try { await result.current.doSomething('fail'); } catch {}
    });
    expect(result.current.error).toBeInstanceOf(Error);
  });
});
```

### Organisms — Integration with Mocked Query

```tsx
// MembershipCard.test.tsx
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { MembershipCard } from './MembershipCard';

const server = setupServer(
  http.get('/api/memberships/1', () => HttpResponse.json({
    id: '1', name: 'Gold', price: 50000, duration: 30
  }))
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('MembershipCard', () => {
  it('loads and displays membership data', async () => {
    render(<MembershipCard membershipId="1" />);
    
    expect(screen.getByText('Cargando...')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(screen.getByText('Gold')).toBeInTheDocument();
      expect(screen.getByText('$50,000')).toBeInTheDocument();
    });
  });

  it('shows error on failed load', async () => {
    server.use(
      http.get('/api/memberships/1', () => HttpResponse.json({ error: 'Not found' }, { status: 404 }))
    );
    
    render(<MembershipCard membershipId="1" />);
    
    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
```

### Pages — Full Flow with RHF + Query

```tsx
// AssignMembershipPage.test.tsx
import { render, screen, waitFor } from '@/test-utils';
import userEvent from '@testing-library/user-event';
import { http, HttpResponse } from 'msw';
import { setupServer } from 'msw/node';
import { AssignMembershipPage } from '@/pages/AssignMembershipPage';

const server = setupServer(
  http.get('/api/members', () => HttpResponse.json([
    { id: '1', name: 'Juan', lastname: 'Pérez', phone: '3001234567' }
  ])),
  http.get('/api/memberships', () => HttpResponse.json([
    { id: '1', name: 'Gold', price: 50000, duration: 30 }
  ])),
  http.post('/api/memberships/assign', () => HttpResponse.json({ success: true }))
);

beforeAll(() => server.listen());
afterEach(() => server.resetHandlers());
afterAll(() => server.close());

describe('AssignMembershipPage', () => {
  it('completes full assignment flow', async () => {
    render(<AssignMembershipPage />);
    
    // Wait for data
    await waitFor(() => expect(screen.getByText('Juan Pérez')).toBeInTheDocument());
    
    // Select member
    await userEvent.selectOptions(screen.getByLabelText('Miembro'), '1');
    
    // Select membership
    await userEvent.selectOptions(screen.getByLabelText('Membresía'), '1');
    
    // Fill multiplier
    await userEvent.clear(screen.getByLabelText('Multiplicador'));
    await userEvent.type(screen.getByLabelText('Multiplicador'), '2');
    
    // Submit
    await userEvent.click(screen.getByRole('button', { name: 'Asignar' }));
    
    await waitFor(() => {
      expect(screen.getByText(/asignada/i)).toBeInTheDocument();
    });
  });
});
```

## Test Utilities (`src/test-utils.tsx`)

```tsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { render, RenderOptions } from '@testing-library/react';
import { ReactElement, ReactNode, useState } from 'react';
import { vi } from 'vitest';

const createTestQueryClient = () =>
  new QueryClient({
    defaultOptions: {
      queries: { retry: false, gcTime: 0, refetchOnWindowFocus: false },
      mutations: { retry: false },
    },
  });

interface WrapperProps {
  children: ReactNode;
  queryClient?: QueryClient;
}

const Wrapper = ({ children, queryClient = createTestQueryClient() }: WrapperProps) => (
  <QueryClientProvider client={queryClient}>
    {children}
    <ReactQueryDevtools initialIsOpen={false} />
  </QueryClientProvider>
);

export const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: Wrapper, ...options });

export * from '@testing-library/react';
export { customRender as render };
```

## Running Tests

```bash
# All tests
npm test

# Watch mode
npm test -- --watch

# Coverage
npm test -- --coverage

# Specific file
npm test Button.test.tsx

# By pattern
npm test -- --testNamePattern="Button"
```

## Coverage Targets

| Layer | Target |
|-------|--------|
| Atoms / Utils / Hooks | 90%+ |
| Molecules | 80%+ |
| Organisms | 70%+ |
| Pages | 60%+ (integration) |

## Common Assertions

```tsx
// Roles (accessibility)
expect(screen.getByRole('button', { name: /submit/i })).toBeInTheDocument();
expect(screen.getByRole('textbox', { name: /email/i })).toHaveValue('test@test.com');
expect(screen.getByRole('alert')).toHaveTextContent('Error message');

// State
expect(screen.getByRole('button')).toBeDisabled();
expect(screen.getByRole('button')).not.toBeDisabled();
expect(screen.getByRole('checkbox')).toBeChecked();

// Forms
expect(screen.getByLabelText('Email')).toHaveAttribute('aria-invalid', 'true');
expect(screen.getByText('Email inválido')).toBeInTheDocument();

// Async
await waitFor(() => expect(screen.getByText('Loaded')).toBeInTheDocument());
await waitFor(() => expect(screen.queryByText('Loading')).not.toBeInTheDocument());

// Mocks
expect(mockFn).toHaveBeenCalledWith(expectedArg);
expect(mockFn).toHaveBeenCalledTimes(1);
```