import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { BrowserRouter } from 'react-router-dom';
import PlatformDashboardPage from './PlatformDashboardPage';

const mockStats = {
    total_gimnasios: 10,
    gimnasios_activos: 8,
    total_usuarios_staff: 25,
    demo_pendientes: 3,
    demo_contactados: 7,
    ingresos_mes_global: '15000000.00',
    miembros_activos_global: 1200,
    retencion_promedio: '85.5',
};

vi.mock('../../../api/action/platform.api', () => {
    const mockGetPlatformStats = vi.fn();
    return { getPlatformStats: mockGetPlatformStats };
});

import * as platformApi from '../../../api/action/platform.api';

describe('PlatformDashboardPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(platformApi.getPlatformStats).mockResolvedValue(mockStats);
    });

    const renderPage = () => render(
        <BrowserRouter>
            <PlatformDashboardPage />
        </BrowserRouter>
    );

    it('renderiza 4 tarjetas de estadísticas principales', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText('Gimnasios Totales')).toBeInTheDocument());

        expect(screen.getByText('10')).toBeInTheDocument(); // total_gimnasios
        expect(screen.getByText('8')).toBeInTheDocument(); // gimnasios_activos
        expect(screen.getByText('25')).toBeInTheDocument(); // total_usuarios_staff
        // demo_pendientes aparece en tarjeta Y en sección demos - buscamos en la tarjeta
        expect(screen.getByText('Demos Pendientes')).toBeInTheDocument();
        const cards = screen.getAllByRole('heading', { level: 2 });
        const demoCardValue = cards.find(el => el.textContent === '3' && el.closest('div')?.textContent?.includes('Demos Pendientes'));
        expect(demoCardValue).toBeInTheDocument();
    });

    it('muestra ingresos del mes formateados en COP', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText(/Ingresos Mes/)).toBeInTheDocument());
        // es-CO currency format: "15.000.000 COP" or "COP 15.000.000"
        expect(screen.getByText(/15\.000\.000/)).toBeInTheDocument();
    });

    it('muestra miembros activos globales y retención promedio', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText(/Miembros Activos/)).toBeInTheDocument());
        expect(screen.getByText('1.200')).toBeInTheDocument();
        expect(screen.getByText('85.5%')).toBeInTheDocument();
    });

    it('muestra estado de carga inicial', () => {
        vi.mocked(platformApi.getPlatformStats).mockImplementation(() => new Promise(() => {}));
        renderPage();
        expect(screen.getByText('Cargando estadísticas...')).toBeInTheDocument();
    });

    it('muestra error si la API falla', async () => {
        vi.mocked(platformApi.getPlatformStats).mockRejectedValue(new Error('Network error'));
        renderPage();

        await waitFor(() => expect(screen.getByText(/Error al cargar/)).toBeInTheDocument());
    });
});