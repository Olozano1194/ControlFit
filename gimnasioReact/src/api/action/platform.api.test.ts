import { describe, it, expect, vi, beforeEach } from 'vitest';

vi.mock('../axios/axios.private', () => {
    const mockGet = vi.fn();
    const mockPost = vi.fn();
    const mockPatch = vi.fn();
    return { axiosPrivate: { get: mockGet, post: mockPost, patch: mockPatch } };
});

import { axiosPrivate } from '../axios/axios.private';
import {
    getPlatformStats,
    getGimnasios,
    getGimnasioDetail,
    toggleGimnasioActive,
    createGimnasio,
} from './platform.api';
import type { PlatformStats, PaginatedResponse, GimnasioPlatform } from '../../model/dto/platform.dto';

const mockedAxios = vi.mocked(axiosPrivate, true);

const mockStats: PlatformStats = {
    total_gimnasios: 10,
    gimnasios_activos: 8,
    total_usuarios_staff: 25,
    demo_pendientes: 3,
    demo_contactados: 5,
    ingresos_mes_global: '15000000.00',
    miembros_activos_global: 1200,
    retencion_promedio: '85.5',
};

const mockPaginated: PaginatedResponse<GimnasioPlatform> = {
    count: 2,
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
    ],
};

describe('platform.api', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('getPlatformStats hace GET a /platform/stats/ y devuelve los datos', async () => {
        mockedAxios.get.mockResolvedValue({ data: mockStats });

        const result = await getPlatformStats();

        expect(mockedAxios.get).toHaveBeenCalledWith('/platform/stats/');
        expect(result).toEqual(mockStats);
        expect(result.total_gimnasios).toBe(10);
        expect(result.retencion_promedio).toBeCloseTo(85.5);
    });

    it('getGimnasios devuelve forma paginada (count/results)', async () => {
        mockedAxios.get.mockResolvedValue({ data: mockPaginated });

        const result = await getGimnasios();

        expect(mockedAxios.get).toHaveBeenCalledWith('/platform/gimnasios/', { params: {} });
        expect(result.count).toBe(2);
        expect(Array.isArray(result.results)).toBe(true);
        expect(result.results[0].name).toBe('Gym Alpha');
    });

    it('getGimnasios pasa page y search como query params', async () => {
        mockedAxios.get.mockResolvedValue({ data: mockPaginated });

        await getGimnasios(2, 'alpha');

        expect(mockedAxios.get).toHaveBeenCalledWith('/platform/gimnasios/', {
            params: { page: 2, search: 'alpha' },
        });
    });

    it('getGimnasioDetail hace GET al detalle con el id', async () => {
        const detail = { ...mockPaginated.results[0], usuarios: [], miembros_activos: [], ultimos_pagos: [] };
        mockedAxios.get.mockResolvedValue({ data: detail });

        const result = await getGimnasioDetail(7);

        expect(mockedAxios.get).toHaveBeenCalledWith('/platform/gimnasios/7/');
        expect(result.id).toBe(1);
    });

    it('toggleGimnasioActive hace PATCH con is_active en el body', async () => {
        const updated = { ...mockPaginated.results[1], is_active: true };
        mockedAxios.patch.mockResolvedValue({ data: updated });

        const result = await toggleGimnasioActive(2, true);

        expect(mockedAxios.patch).toHaveBeenCalledWith('/platform/gimnasios/2/', { is_active: true });
        expect(result.is_active).toBe(true);
    });

    it('createGimnasio hace POST con el DTO en el body', async () => {
        const created = mockPaginated.results[0];
        mockedAxios.post.mockResolvedValue({ data: created });
        const dto = { name: 'Gym Nuevo', address: 'Calle 9', phone: '3009998888' };

        const result = await createGimnasio(dto);

        expect(mockedAxios.post).toHaveBeenCalledWith('/platform/gimnasios/', dto);
        expect(result.name).toBe('Gym Alpha');
    });
});
