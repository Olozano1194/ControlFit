import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ModalWrapper from './eventForm/ModalWrapper';

const renderModal = (onClose = () => {}) =>
    render(
        <ModalWrapper onClose={onClose} title="Nuevo Evento">
            <button>Primero</button>
            <button>Último</button>
        </ModalWrapper>
    );

describe('ModalWrapper - accesibilidad', () => {
    it('marca el contenedor como dialog modal con nombre accesible', () => {
        renderModal();

        const dialog = screen.getByRole('dialog');
        expect(dialog).toHaveAttribute('aria-modal', 'true');
        expect(dialog).toHaveAccessibleName('Nuevo Evento');
    });

    it('mueve el foco al primer elemento enfocable al montar', () => {
        renderModal();

        expect(screen.getByRole('button', { name: 'Cerrar' })).toHaveFocus();
    });

    it('cierra al presionar Escape', async () => {
        const onClose = vi.fn();
        const user = userEvent.setup();
        renderModal(onClose);

        await user.keyboard('{Escape}');

        expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('atrapa el foco: Tab desde el último vuelve al primero', async () => {
        const user = userEvent.setup();
        renderModal();

        const last = screen.getByRole('button', { name: 'Último' });
        last.focus();

        await user.tab();

        expect(screen.getByRole('button', { name: 'Cerrar' })).toHaveFocus();
    });

    it('atrapa el foco: Shift+Tab desde el primero va al último', async () => {
        const user = userEvent.setup();
        renderModal();

        const close = screen.getByRole('button', { name: 'Cerrar' });
        close.focus();

        await user.tab({ shift: true });

        expect(screen.getByRole('button', { name: 'Último' })).toHaveFocus();
    });

    it('restaura el foco al elemento previo al desmontar', () => {
        const trigger = document.createElement('button');
        trigger.textContent = 'Abrir';
        document.body.appendChild(trigger);
        trigger.focus();

        const { unmount } = renderModal();
        unmount();

        expect(trigger).toHaveFocus();

        document.body.removeChild(trigger);
    });
});
