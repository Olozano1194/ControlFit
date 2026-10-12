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

describe('DemoRequestsPage - render', () => {
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
        let resolveMutation: (value: unknown) => void;
        const mutationPromise = new Promise<unknown>((resolve) => {
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
});