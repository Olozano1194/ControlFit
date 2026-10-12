import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, act } from '@testing-library/react';
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
    deleteDemoRequest: vi.fn(),
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

describe('DemoRequestsPage - toggle success toasts', () => {
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

    it('prevents double-click during loading state', async () => {
        let resolveMutation: (value: unknown) => void;
        const mutationPromise = new Promise<unknown>((resolve) => {
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
});