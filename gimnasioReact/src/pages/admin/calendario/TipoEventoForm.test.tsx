import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import TipoEventoForm from './TipoEventoForm';
import { createTipoEvento } from '../../../api/action/calendario.api';

vi.mock('../../../api/action/calendario.api', () => ({
    createTipoEvento: vi.fn(),
    updateTipoEvento: vi.fn(),
}));

describe('TipoEventoForm - accesibilidad', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('expone un dialog modal con nombre accesible', () => {
        render(<TipoEventoForm isOpen onClose={() => {}} onSuccess={() => {}} />);

        const dialog = screen.getByRole('dialog');
        expect(dialog).toHaveAttribute('aria-modal', 'true');
        expect(dialog).toHaveAccessibleName('Nuevo Tipo de Evento');
    });

    it('asocia cada control con su label', () => {
        render(<TipoEventoForm isOpen onClose={() => {}} onSuccess={() => {}} />);

        expect(screen.getByLabelText('Nombre *')).toHaveAttribute('id', 'nombre');
        expect(screen.getByLabelText('Color *')).toHaveAttribute('id', 'color');
    });

    it('anuncia los errores de validación con role=alert y aria-describedby', async () => {
        const user = userEvent.setup();
        render(<TipoEventoForm isOpen onClose={() => {}} onSuccess={() => {}} />);

        await user.click(screen.getByRole('button', { name: 'Crear Tipo' }));

        const nombre = screen.getByLabelText('Nombre *');
        expect(nombre).toHaveAttribute('aria-invalid', 'true');
        expect(nombre).toHaveAttribute('aria-describedby', 'nombre-error');
        expect(screen.getByText('El nombre es requerido')).toBeInTheDocument();
        expect(screen.getAllByRole('alert').length).toBeGreaterThan(0);
    });

    it('deshabilita el submit y muestra "Guardando..." mientras envía', async () => {
        // Promesa que nunca resuelve: mantiene el estado de envío.
        vi.mocked(createTipoEvento).mockReturnValue(
            new Promise(() => {}) as ReturnType<typeof createTipoEvento>
        );
        const user = userEvent.setup();
        render(<TipoEventoForm isOpen onClose={() => {}} onSuccess={() => {}} />);

        await user.type(screen.getByLabelText('Nombre *'), 'Yoga');
        await user.click(screen.getByRole('button', { name: 'Crear Tipo' }));

        expect(
            screen.getByRole('button', { name: 'Guardando...' })
        ).toBeDisabled();
    });

    it('cierra el diálogo al presionar Escape', async () => {
        const onClose = vi.fn();
        const user = userEvent.setup();
        render(<TipoEventoForm isOpen onClose={onClose} onSuccess={() => {}} />);

        await user.keyboard('{Escape}');

        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
