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

describe('DemoRequestsPage - toggle error toasts', () => {
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
});