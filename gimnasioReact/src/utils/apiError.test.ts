import { describe, it, expect } from 'vitest';
import { AxiosError, AxiosHeaders } from 'axios';
import { getApiErrorMessage } from './apiError';

const axiosErrorWith = (data: unknown, status = 400): AxiosError => {
    const error = new AxiosError('Request failed with status code 400');
    error.response = {
        data,
        status,
        statusText: 'Bad Request',
        headers: {},
        config: { headers: new AxiosHeaders() },
    };
    return error;
};

describe('getApiErrorMessage', () => {
    it('extrae el detalle de un error DRF', () => {
        expect(
            getApiErrorMessage(axiosErrorWith({ detail: 'No tiene permisos' }), 'fallback')
        ).toBe('No tiene permisos');
    });

    it('extrae un error de validación de campo', () => {
        expect(
            getApiErrorMessage(
                axiosErrorWith({ titulo: ['El título es requerido'] }),
                'fallback'
            )
        ).toBe('El título es requerido');
    });

    it('extrae non_field_errors (validación a nivel de objeto)', () => {
        expect(
            getApiErrorMessage(
                axiosErrorWith({ non_field_errors: ['fecha_fin must be after fecha_inicio'] }),
                'fallback'
            )
        ).toBe('fecha_fin must be after fecha_inicio');
    });

    it('extrae mensajes anidados de serializers anidados', () => {
        expect(
            getApiErrorMessage(
                axiosErrorWith({ tipo: { nombre: ['El nombre es requerido'] } }),
                'fallback'
            )
        ).toBe('El nombre es requerido');
    });

    it('usa el fallback cuando el body es HTML (500 con DEBUG)', () => {
        expect(
            getApiErrorMessage(
                axiosErrorWith('<!DOCTYPE html><html>...</html>', 500),
                'Error al guardar'
            )
        ).toBe('Error al guardar');
    });

    it('usa el fallback en errores de red (sin response)', () => {
        expect(
            getApiErrorMessage(new AxiosError('Network Error'), 'Sin conexión')
        ).toBe('Sin conexión');
    });

    it('usa el fallback cuando el body no trae mensajes', () => {
        expect(getApiErrorMessage(axiosErrorWith({}), 'Error al guardar')).toBe(
            'Error al guardar'
        );
    });

    it('devuelve el message de un Error común', () => {
        expect(getApiErrorMessage(new Error('boom'), 'fallback')).toBe('boom');
    });

    it('usa el fallback para valores no-Error', () => {
        expect(getApiErrorMessage('algo', 'fallback')).toBe('fallback');
        expect(getApiErrorMessage(null, 'fallback')).toBe('fallback');
    });
});
