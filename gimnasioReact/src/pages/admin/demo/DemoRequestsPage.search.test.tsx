import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
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

describe('DemoRequestsPage - search', () => {
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
        {
            id: 3,
            nombre: 'Carlos López',
            email: 'carlos@otro.com',
            telefono: '3009998877',
            nombre_gimnasio: 'Gym Alpha',
            estado: 'cancelada' as const,
            fecha_solicitud: '2024-01-13T10:00:00Z',
            gym_creado: null,
            email_sent: false,
        },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        (demoRequestsApi.getDemoRequests as vi.Mock).mockResolvedValue(mockDemoRequests);
    });

    afterEach(() => {
        vi.resetAllMocks();
    });

    it('filters by contact name', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
            expect(screen.getByText('Gym Pro')).toBeInTheDocument();
            expect(screen.getByText('Gym Alpha')).toBeInTheDocument();
        });

        // Search by contact name
        const searchInput = screen.getByPlaceholderText(/Buscar por nombre, gimnasio, email o teléfono/);
        await userEvent.type(searchInput, 'Juan');

        // Should only show Juan's row
        await waitFor(() => {
            expect(screen.getByText('Juan Pérez')).toBeInTheDocument();
            expect(screen.queryByText('María García')).not.toBeInTheDocument();
            expect(screen.queryByText('Carlos López')).not.toBeInTheDocument();
        });
    });

    it('filters by gym name', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        // Search by gym name
        const searchInput = screen.getByPlaceholderText(/Buscar por nombre, gimnasio, email o teléfono/);
        await userEvent.type(searchInput, 'Gym Pro');

        // Should only show María's row
        await waitFor(() => {
            expect(screen.getByText('Gym Pro')).toBeInTheDocument();
            expect(screen.getByText('María García')).toBeInTheDocument();
            expect(screen.queryByText('Gym Test')).not.toBeInTheDocument();
            expect(screen.queryByText('Gym Alpha')).not.toBeInTheDocument();
        });
    });

    it('filters by email', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('juan@example.com')).toBeInTheDocument();
        });

        // Search by email
        const searchInput = screen.getByPlaceholderText(/Buscar por nombre, gimnasio, email o teléfono/);
        await userEvent.type(searchInput, 'maria@example.com');

        // Should only show María's row
        await waitFor(() => {
            expect(screen.getByText('maria@example.com')).toBeInTheDocument();
            expect(screen.queryByText('juan@example.com')).not.toBeInTheDocument();
        });
    });

    it('filters by phone number', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('3009998877')).toBeInTheDocument();
        });

        // Search by phone
        const searchInput = screen.getByPlaceholderText(/Buscar por nombre, gimnasio, email o teléfono/);
        await userEvent.type(searchInput, '3009998877');

        // Should only show Carlos's row
        await waitFor(() => {
            expect(screen.getByText('Carlos López')).toBeInTheDocument();
            expect(screen.queryByText('Juan Pérez')).not.toBeInTheDocument();
            expect(screen.queryByText('María García')).not.toBeInTheDocument();
        });
    });

    it('shows all results when search is cleared', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        // Search and then clear
        const searchInput = screen.getByPlaceholderText(/Buscar por nombre, gimnasio, email o teléfono/);
        await userEvent.type(searchInput, 'Juan');
        await waitFor(() => {
            expect(screen.queryByText('María García')).not.toBeInTheDocument();
        });

        // Clear search
        await userEvent.clear(searchInput);

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
            expect(screen.getByText('Gym Pro')).toBeInTheDocument();
            expect(screen.getByText('Gym Alpha')).toBeInTheDocument();
        });
    });

    it('shows no results for non-matching search', async () => {
        render(<DemoRequestsPage />, { wrapper: createWrapper() });

        await waitFor(() => {
            expect(screen.getByText('Gym Test')).toBeInTheDocument();
        });

        // Search for non-existent term
        const searchInput = screen.getByPlaceholderText(/Buscar por nombre, gimnasio, email o teléfono/);
        await userEvent.type(searchInput, 'NoExiste');

        await waitFor(() => {
            expect(screen.queryByText('Gym Test')).not.toBeInTheDocument();
            expect(screen.queryByText('Gym Pro')).not.toBeInTheDocument();
            expect(screen.queryByText('Gym Alpha')).not.toBeInTheDocument();
        });
    });
});