import { useCallback, useMemo } from 'react';
import { CalendarEvent } from './calendarTypes';
import { Calendar, dateFnsLocalizer, type SlotInfo } from 'react-big-calendar';
import { es } from 'date-fns/locale/es';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import withDragAndDrop, { type EventInteractionArgs } from 'react-big-calendar/lib/addons/dragAndDrop';

interface CalendarViewProps {
    events: CalendarEvent[];
    onSelectEvent: (event: CalendarEvent) => void;
    onSelectSlot: (slotInfo: SlotInfo) => void;
    onEventDrop: (args: EventInteractionArgs<CalendarEvent>) => void;
    onEventResize: (args: EventInteractionArgs<CalendarEvent>) => void;
    isAdmin: boolean;
}

const CalendarView = ({ events, onSelectEvent, onSelectSlot, onEventDrop, onEventResize, isAdmin }: CalendarViewProps) => {

    // ─── Localizer ───────────────────────────────────────────────────────────────
    const locales = { es };
    const localizer = dateFnsLocalizer({
        format,
        parse,
        startOfWeek,
        getDay,
        locales,
    });

    // Elige texto blanco u oscuro según la luminancia del color de fondo
    // para mantener legibilidad con colores claros (ej: verde claro).
    const getContrastText = (hexColor: string): string => {
        const hex = hexColor.replace('#', '');
        if (hex.length !== 6) return '#fff';
        const r = parseInt(hex.slice(0, 2), 16);
        const g = parseInt(hex.slice(2, 4), 16);
        const b = parseInt(hex.slice(4, 6), 16);
        const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255;
        return luminance > 0.6 ? '#1f2937' : '#fff';
    };

    const eventPropGetter = useCallback(
        (event: CalendarEvent) => {
            const color = event.resource?.tipo_detalle?.color || '#3B82F6';
            return {
                style: {
                    backgroundColor: color,
                    borderColor: color,
                    borderRadius: '4px',
                    color: getContrastText(color),
                    fontSize: '0.8rem',
                    border: 'none',
                },
            };
        },
        []
    );

    // Wrapper condicional: admin obtiene drag & drop, recepción no.
    // useMemo mantiene la identidad del componente estable entre renders.
    const DnDCalendar = useMemo(
        () =>
            (isAdmin ? withDragAndDrop<CalendarEvent>(Calendar) : Calendar) as ReturnType<
                typeof withDragAndDrop<CalendarEvent>
            >,
        [isAdmin]
    );

    // Message i18n
    const messages = {
        next: 'Siguiente',
        previous: 'Anterior',
        today: 'Hoy',
        month: 'Mes',
        week: 'Semana',
        day: 'Día',
        agenda: 'Agenda',
        date: 'Fecha',
        time: 'Hora',
        event: 'Evento',
        noEventsInRange: 'No hay eventos en este rango.',
        showMore: (count: number) => `+ Ver más (${count})`,
    }

    return (
        <DnDCalendar
            localizer={localizer}
            events={events}
            startAccessor="start"
            endAccessor="end"
            style={{ height: 650 }}
            views={['month', 'week', 'day', 'agenda']}
            defaultView="month"
            eventPropGetter={eventPropGetter}
            onSelectEvent={onSelectEvent}
            onSelectSlot={onSelectSlot}
            onEventDrop={onEventDrop}
            onEventResize={onEventResize}
            selectable
            resizable={isAdmin}
            messages={messages}
            popup
        />
    );
}
export default CalendarView;