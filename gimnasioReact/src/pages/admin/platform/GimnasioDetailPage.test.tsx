import { render, screen, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import GimnasioDetailPage from './GimnasioDetailPage';
import type { GimnasioPlatformDetail } from '../../../model/dto/platform.dto';

const mockGimnasioDetail: GimnasioPlatformDetail = {
    id: 1,
    name: 'Gym Alpha',
    address: 'Calle 1',
    phone: '3001112233',
    is_active: true,
    created_at: '2026-01-15T10:00:00Z',
    usuarios_count: 5,
    miembros_activos_count: 150,
    ingresos_mes: '5000000.00',
    usuarios: [
        { id: 1, email: 'admin@alpha.com', name: 'Admin', lastname: 'Alpha', roles: 'admin', is_active: true },
        { id: 2, email: 'recepcion@alpha.com', name: 'Recep', lastname: 'Alpha', roles: 'recepcion', is_active: true },
    ],
    miembros_activos: [
        { id: 1, name: 'Juan', lastname: 'Perez', membresia: 'Premium', dateFinal: '2026-12-31', saldo_pendiente: '0' },
        { id: 2, name: 'Maria', lastname: 'Lopez', membresia: 'Basica', dateFinal: '2026-10-15', saldo_pendiente: '50000' },
    ],
    ultimos_pagos: [
        { id: 1, monto: '100000.00', fecha_pago: '2026-08-20T10:00:00Z', metodo_pago: 'efectivo', miembro_name: 'Juan', miembro_lastname: 'Perez', membresia_name: 'Premium' },
        { id: 2, monto: '50000.00', fecha_pago: '2026-08-19T15:00:00Z', metodo_pago: 'tarjeta', miembro_name: 'Maria', miembro_lastname: 'Lopez', membresia_name: 'Basica' },
    ],
};

vi.mock('../../../api/action/platform.api', () => {
    const mockGetGimnasioDetail = vi.fn();
    return { getGimnasioDetail: mockGetGimnasioDetail };
});

import * as platformApi from '../../../api/action/platform.api';

describe('GimnasioDetailPage', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        vi.mocked(platformApi.getGimnasioDetail).mockResolvedValue(mockGimnasioDetail);
    });

    const renderPage = () => render(
        <MemoryRouter initialEntries={['/platform/gimnasios/1']}>
            <Routes>
                <Route path="/platform/gimnasios/:id" element={<GimnasioDetailPage />} />
            </Routes>
        </MemoryRouter>
    );

    it('renderiza header con nombre del gimnasio', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText('Gym Alpha')).toBeInTheDocument());
        expect(screen.getByText('Calle 1')).toBeInTheDocument();
    });

    it('muestra sección de usuarios del gimnasio', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText(/Usuarios del Gimnasio/)).toBeInTheDocument());
        expect(screen.getByText('admin@alpha.com')).toBeInTheDocument();
        expect(screen.getByText('recepcion@alpha.com')).toBeInTheDocument();
    });

    it('muestra sección de miembros activos con membresía y fecha fin', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText(/Miembros Activos \(\d\)/)).toBeInTheDocument());
        // Verificar que hay contenido en la tabla de miembros (header "Membresía" aparece 2 veces - una en cada tabla)
        const membresiaHeaders = screen.getAllByText('Membresía');
        expect(membresiaHeaders.length).toBe(2);
        expect(screen.getByText('Fecha Fin')).toBeInTheDocument();
    });

    it('muestra saldo pendiente en miembros', async () => {
        renderPage();

        // formatCurrency devuelve "$ 50.000" - usar getAllByText y verificar que existe
        await waitFor(() => {
            const matches = screen.getAllByText(/50\.000/);
            expect(matches.length).toBeGreaterThan(0);
        });
    });

    it('muestra sección de últimos pagos', async () => {
        renderPage();

        await waitFor(() => expect(screen.getByText(/Últimos Pagos/)).toBeInTheDocument());
        // Verificar header "Método" de la tabla de pagos
        expect(screen.getByText('Método')).toBeInTheDocument();
        expect(screen.getByText('Monto')).toBeInTheDocument();
    });

    it('muestra estado de carga', () => {
        vi.mocked(platformApi.getGimnasioDetail).mockImplementation(() => new Promise(() => {}));
        renderPage();
        expect(screen.getByText('Cargando detalle...')).toBeInTheDocument();
    });

    it('muestra error si la API falla', async () => {
        vi.mocked(platformApi.getGimnasioDetail).mockRejectedValue(new Error('Network error'));
        renderPage();

        await waitFor(() => expect(screen.getByText(/Error al cargar/)).toBeInTheDocument());
    });
});