import { render, screen, waitFor, fireEvent, act } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import GimnasiosPage from './GimnasiosPage';

const mockGimnasiosPage = {
    count: 3,
    next: null,
    previous: null,
    results: [
        {
            id: 1,
            name: 'Gym Alpha',
            address: 'Calle 1',
            phone: '3001112233',
            is_active: true,
            created_at: '2026-01-15T10:00:00Z',
            usuarios_count: 5,
            miembros_activos_count: 150,
            ingresos_mes: '5000000.00',
        },
        {
            id: 2,
            name: 'Gym Beta',
            address: 'Carrera 2',
            phone: '3004445566',
            is_active: false,
            created_at: '2026-02-20T10:00:00Z',
            usuarios_count: 3,
            miembros_activos_count: 80,
            ingresos_mes: '2500000.00',
        },
        {
            id: 3,
            name: 'Gym Gamma',
            address: 'Avenida 3',
            phone: '3007778899',
            is_active: true,
            created_at: '2026-03-10T10:00:00Z',
            usuarios_count: 4,
            miembros_activos_count: 200,
            ingresos_mes: '7500000.00',
        },
    ],
};

vi.mock('../../../api/action/platform.api', () => {
    const mockGetGimnasios = vi.fn();
    const mockToggleGimnasioActive = vi.fn();
    return { getGimnasios: mockGetGimnasios, toggleGimnasioActive: mockToggleGimnasioActive };
});

import * as platformApi from '../../../api/action/platform.api';

describe('GimnasiosPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(platformApi.getGimnasios).mockResolvedValue(mockGimnasiosPage);
    });

    const renderPage = () => render(
        <BrowserRouter>
            <GimnasiosPage />
        </BrowserRouter>
    );

    it('renderiza tabla con gimnasios', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText('Gym Alpha')).toBeInTheDocument());
        expect(screen.getByText('Gym Beta')).toBeInTheDocument();
        expect(screen.getByText('Gym Gamma')).toBeInTheDocument();
    });

    it('muestra badges de estado (activo/inactivo)', async () => {
        renderPage();

        // Buscar los badges - hay 2 "Activo" (Gym Alpha y Gamma) y 1 "Inactivo" (Gym Beta)
        await waitFor(() => {
            const activos = screen.getAllByText('Activo');
            const inactivos = screen.getAllByText('Inactivo');
            expect(activos.length).toBe(2);
            expect(inactivos.length).toBe(1);
        });
    });

    it('muestra columnas: usuarios, miembros activos, ingresos mes', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText('5')).toBeInTheDocument()); // usuarios_count Gym Alpha
        expect(screen.getByText('150')).toBeInTheDocument(); // miembros_activos_count Gym Alpha
        expect(screen.getByText(/5\.000\.000/)).toBeInTheDocument(); // ingresos_mes Gym Alpha
    });

    it('paginación: 3 gimnasios caben en página default (20)', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText('Gym Gamma')).toBeInTheDocument());
        // No debe haber paginación visible con solo 3 items y page_size 20
    });

    it('botón toggle is_active llama a la API', async () => {
        vi.mocked(platformApi.toggleGimnasioActive).mockResolvedValue({ ...mockGimnasiosPage.results[1], is_active: true });
        renderPage();

        await waitFor(() => expect(screen.getByText('Gym Beta')).toBeInTheDocument());
        // Buscar el botón "Activar" específicamente en la fila de Gym Beta
        const toggleBtn = screen.getByRole('button', { name: 'Activar' });
        toggleBtn.click();

        await waitFor(() => expect(platformApi.toggleGimnasioActive).toHaveBeenCalledWith(2, true));
    });

    it('muestra estado de carga', () => {
        vi.mocked(platformApi.getGimnasios).mockImplementation(() => new Promise(() => {}));
        renderPage();
        expect(screen.getByText('Cargando gimnasios...')).toBeInTheDocument();
    });

    it('muestra error si la API falla', async () => {
        vi.mocked(platformApi.getGimnasios).mockRejectedValue(new Error('Network error'));
        renderPage();

        await waitFor(() => expect(screen.getByText(/Error al cargar/)).toBeInTheDocument());
    });

    it('buscador llama a la API con el término de búsqueda (debounce 500ms)', async () => {
        vi.useFakeTimers();
        try {
            renderPage();
            await act(async () => { await Promise.resolve(); });

            const input = screen.getByPlaceholderText('Buscar gimnasio...');
            fireEvent.change(input, { target: { value: 'Alpha' } });

            expect(vi.mocked(platformApi.getGimnasios)).not.toHaveBeenCalledWith(expect.anything(), 'alpha');

            await act(async () => { await vi.advanceTimersByTimeAsync(600); });

            expect(vi.mocked(platformApi.getGimnasios)).toHaveBeenCalledWith(1, 'alpha');
        } finally {
            vi.useRealTimers();
        }
    });
});