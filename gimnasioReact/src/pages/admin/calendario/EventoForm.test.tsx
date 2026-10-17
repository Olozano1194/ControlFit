import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { useReducer } from 'react';
import EventoForm from './EventoForm';

vi.mock('../../../api/action/calendario.api', () => ({
    createEvento: vi.fn(),
    updateEvento: vi.fn(),
    getTiposEvento: vi.fn().mockResolvedValue([]),
}));

// Reproduce el caller real: CalendarioPage construye `initialDates` inline en el
// JSX, así que el objeto es nuevo en cada render del padre.
const Harness = ({ onClose = () => {} }: { onClose?: () => void }) => {
    const [, forceRender] = useReducer((n: number) => n + 1, 0);

    return (
        <>
            <button onClick={forceRender}>rerender parent</button>
            <EventoForm
                isOpen
                onClose={onClose}
                onSuccess={() => {}}
                initialDates={{
                    start: '2026-10-16T09:00',
                    end: '2026-10-16T10:00',
                }}
            />
        </>
    );
};

describe('EventoForm - prefill desde slot', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('precarga las fechas del slot clickeado', async () => {
        const { container } = render(<Harness />);
        await screen.findByText('Fecha de inicio');

        expect(container.querySelector('input[name="fecha_inicio"]')).toHaveValue(
            '2026-10-16T09:00'
        );
        expect(container.querySelector('input[name="fecha_fin"]')).toHaveValue(
            '2026-10-16T10:00'
        );
    });

    it('no resetea el formulario cuando el padre re-renderiza con un initialDates nuevo', async () => {
        const user = userEvent.setup();
        const { container } = render(<Harness />);
        await screen.findByText('Fecha de inicio');

        const titulo = container.querySelector('input[name="titulo"]')!;
        await user.type(titulo, 'Spinning');
        expect(titulo).toHaveValue('Spinning');

        await user.click(screen.getByText('rerender parent'));

        expect(container.querySelector('input[name="titulo"]')).toHaveValue('Spinning');
    });
});

describe('EventoForm - accesibilidad', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('expone un dialog modal con nombre accesible', () => {
        render(<Harness />);

        const dialog = screen.getByRole('dialog');
        expect(dialog).toHaveAttribute('aria-modal', 'true');
        expect(dialog).toHaveAccessibleName('Nuevo Evento');
    });

    it('asocia cada control con su label', () => {
        render(<Harness />);

        expect(screen.getByLabelText('Título *')).toHaveAttribute('id', 'titulo');
        expect(screen.getByLabelText('Fecha de inicio')).toHaveAttribute('id', 'fecha_inicio');
        expect(screen.getByLabelText('Fecha de fin')).toHaveAttribute('id', 'fecha_fin');
        expect(screen.getByLabelText('Descripción')).toHaveAttribute('id', 'descripcion');
        expect(screen.getByLabelText('Tipo de Evento')).toHaveAttribute('id', 'tipo');
        expect(screen.getByLabelText('Relacionado a')).toHaveAttribute('id', 'relacion_tipo');
        expect(screen.getByLabelText('ID de relación')).toHaveAttribute('id', 'relacion_id');
    });

    it('anuncia los errores de validación con role=alert y aria-describedby', async () => {
        const user = userEvent.setup();
        // Sin initialDates: el formulario arranca vacío y dispara los `required`.
        render(<EventoForm isOpen onClose={() => {}} onSuccess={() => {}} />);

        await user.click(screen.getByRole('button', { name: 'Crear Evento' }));

        const titulo = screen.getByLabelText('Título *');
        expect(titulo).toHaveAttribute('aria-invalid', 'true');
        expect(titulo).toHaveAttribute('aria-describedby', 'titulo-error');
        expect(screen.getByText('El título es requerido')).toBeInTheDocument();

        const inicio = screen.getByLabelText('Fecha de inicio');
        expect(inicio).toHaveAttribute('aria-invalid', 'true');
        expect(inicio).toHaveAttribute('aria-describedby', 'fecha_inicio-error');

        expect(screen.getAllByRole('alert').length).toBeGreaterThan(0);
    });

    it('cierra el diálogo al presionar Escape', async () => {
        const onClose = vi.fn();
        const user = userEvent.setup();
        render(<Harness onClose={onClose} />);

        await user.keyboard('{Escape}');

        expect(onClose).toHaveBeenCalledTimes(1);
    });
});
