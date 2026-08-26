import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { ReactNode } from 'react';
import DemoRequestsPage from './DemoRequestsPage';
import * as demoRequestsApi from '../../../api/action/demoRequests.api';

// Mock the API module
vi.mock('../../../api/action/demoRequests.api', () => ({
    getDemoRequests: vi.fn(),
    updateDemoRequestEstado: vi.fn(),
}));

// Test wrapper with QueryClient and Toaster
const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: { retry: false },
            mutations: { retry: false },
        },
    });

    return ({ children }: { children: ReactNode }) => (
        <QueryClientProvider client={queryClient}>
            {children}
            <Toaster />
        </QueryClientProvider>
    );
};

describe('DemoRequestsPage', () => {
    const mockDemoRequests = [
        {
            id: 1,
            nombre: 'Juan Pérez',
            email: 'juan@example.com',
            telefono: '3001234567',
            nombre_gimnasio: 'Gym Test',
            estado: 'pendiente' as const,
            fecha_solicitud: '2024-01-15T10:00:00Z',
            gym_creado: null,
            email_sent: false,
        },
        {
            id: 2,
            nombre: 'María García',
            email: 'maria@example.com',
            telefono: '3007654321',
            nombre_gimnasio: 'Gym Pro',
            estado: 'contactado' as const,
            fecha_solicitud: '2024-01-14T15:30:00Z',
            gym_creado: {
                id: 10,
                name: 'Gym Pro',
                address: 'Calle 123',
                phone: '3007654321',
                is_active: true,
                created_at: '2024-01-14T16:00:00Z',
            },
            email_sent: true,
        },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        (demoRequestsApi.getDemoRequests as vi.Mock).mockResolvedValue(mockDemoRequests);
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    it('renders demo requests table with correct data', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            // Header text is split: "Solicitudes de" + "Demo" in separate elements
            expect(screen.getByText('Solicitudes de')).toBeInTheDocument();
            expect(screen.getByText('Demo')).toBeInTheDocument();
        });

        expect(screen.getByText('Gym Test')).toBeInTheDocument();
        expect(screen.getByText('Gym Pro')).toBeInTheDocument();
        expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
        expect(screen.getByText('María García')).toBeInTheDocument();
        expect(screen.getByText('juan@example.com')).toBeInTheDocument();
        expect(screen.getByText('maria@example.com')).toBeInTheDocument();
    });

    it('shows loading state on badge click during mutation', async () => {
        let resolveMutation: (value: any) => void;
        const mutationPromise = new Promise((resolve) => {
            resolveMutation = resolve;
        });
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockReturnValue(mutationPromise);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        // Click the first badge (Pendiente -> Contactado)
        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        // Should show loading spinner and "Cargando..." text
        await waitFor(() => {
            expect(screen.getByText('Cargando...')).toBeInTheDocument();
        });

        // Badge should be disabled during loading
        const loadingBadge = screen.getByText('Cargando...').closest('button');
        expect(loadingBadge).toBeDisabled();

        // Resolve the mutation
        const updatedDemo = { ...mockDemoRequests[0], estado: 'contactado' as const };
        act(() => {
            resolveMutation!(updatedDemo);
        });

        // Loading state should be gone
        await waitFor(() => {
            expect(screen.queryByText('Cargando...')).not.toBeInTheDocument();
        });
    });

    it('shows success toast with gym_creado on pendiente→contactado transition', async () => {
        const updatedDemo = {
            ...mockDemoRequests[0],
            estado: 'contactado' as const,
            gym_creado: {
                id: 10,
                name: 'Gym Test',
                address: 'Calle 123',
                phone: '3001234567',
                is_active: true,
                created_at: '2024-01-15T11:00:00Z',
            },
            email_sent: true,
        };
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockResolvedValue(updatedDemo);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        await waitFor(() => {
            // Use getAllByText to handle potential duplicates from react-hot-toast in tests
            const toasts = screen.getAllByText(/¡Gimnasio creado!/);
            expect(toasts.length).toBeGreaterThan(0);
            expect(toasts[0]).toHaveTextContent(/Credenciales enviadas a juan@example.com/);
        });
    });

    it('shows revert toast on contactado→pendiente transition with gym_creado null', async () => {
        const updatedDemo = {
            ...mockDemoRequests[1],
            estado: 'pendiente' as const,
            gym_creado: null,
            email_sent: false,
        };
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockResolvedValue(updatedDemo);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Pro')).toBeInTheDocument();
        });

        const contactadoBadge = screen.getByText('Contactado');
        await userEvent.click(contactadoBadge);

        await waitFor(() => {
            const toasts = screen.getAllByText(/Revertido a pendiente/);
            expect(toasts.length).toBeGreaterThan(0);
            expect(toasts[0]).toHaveTextContent(/gimnasio asociado ha sido desactivado/);
        });
    });

    it('shows email duplicate error toast on 400 response with email field', async () => {
        const errorResponse = {
            response: {
                data: {
                    email: ['Este email ya está registrado. Usá otro email o contactá a soporte.'],
                },
            },
        };
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockRejectedValue(errorResponse);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        await waitFor(() => {
            const toasts = screen.getAllByText(/Este email ya está registrado/);
            expect(toasts.length).toBeGreaterThan(0);
        });
    });

    it('handles generic error toast on 500/network error', async () => {
        const errorResponse = {
            response: {
                data: {
                    detail: 'Error interno del servidor',
                },
            },
        };
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockRejectedValue(errorResponse);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        await waitFor(() => {
            const toasts = screen.getAllByText(/Error/);
            expect(toasts.length).toBeGreaterThan(0);
            // Check for either the generic error or the detail message
            const found = toasts.some(t => 
                t.textContent?.includes('Error al actualizar') || 
                t.textContent?.includes('Error interno del servidor') ||
                t.textContent?.includes('No se pudo cambiar')
            );
            expect(found).toBe(true);
        });
    });

    it('does not navigate on success (no window.location change)', async () => {
        const updatedDemo = {
            ...mockDemoRequests[0],
            estado: 'contactado' as const,
            gym_creado: {
                id: 10,
                name: 'Gym Test',
                address: 'Calle 123',
                phone: '3001234567',
                is_active: true,
                created_at: '2024-01-15T11:00:00Z',
            },
            email_sent: true,
        };
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockResolvedValue(updatedDemo);

        const originalLocation = window.location.href;
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        await waitFor(() => {
            const toasts = screen.getAllByText(/¡Gimnasio creado!/);
            expect(toasts.length).toBeGreaterThan(0);
        });

        // Verify no navigation occurred
        expect(window.location.href).toBe(originalLocation);
    });

    it('prevents double-click during loading state', async () => {
        let resolveMutation: (value: any) => void;
        const mutationPromise = new Promise((resolve) => {
            resolveMutation = resolve;
        });
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockReturnValue(mutationPromise);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        // Try to click again while loading
        await userEvent.click(screen.getByText('Cargando...').closest('button')!);

        // Should only have called the API once
        expect(demoRequestsApi.updateDemoRequestEstado).toHaveBeenCalledTimes(1);

        // Resolve the mutation
        act(() => {
            resolveMutation!({ ...mockDemoRequests[0], estado: 'contactado' as const });
        });
    });

    it('shows simple success toast for idempotent state change without gym_creado', async () => {
        const updatedDemo = {
            ...mockDemoRequests[0],
            estado: 'contactado' as const,
            gym_creado: null,
            email_sent: false,
        };
        (demoRequestsApi.updateDemoRequestEstado as vi.Mock).mockResolvedValue(updatedDemo);

        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        const pendienteBadge = screen.getByText('Pendiente');
        await userEvent.click(pendienteBadge);

        await waitFor(() => {
            const toasts = screen.getAllByText(/Estado actualizado: la solicitud ahora está contactada/);
            expect(toasts.length).toBeGreaterThan(0);
        });
    });
});