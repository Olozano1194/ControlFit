import { useCallback, useEffect, useState } from 'react';
import { Calendar, dateFnsLocalizer, Event } from 'react-big-calendar';
import { format, parse, startOfWeek, getDay } from 'date-fns';
import { es } from 'date-fns/locale/es';
import { toast } from 'react-hot-toast';
import { IoClose } from 'react-icons/io5';
import { getEventos, getTiposEvento } from '../../../api/action/calendario.api';
import { EventoCalendario, TipoEvento } from '../../../model/calendario.model';
import 'react-big-calendar/lib/css/react-big-calendar.css';

// ─── Localizer ───────────────────────────────────────────────────────────────

const locales = { es };

const localizer = dateFnsLocalizer({
    format,
    parse,
    startOfWeek,
    getDay,
    locales,
});

// ─── Tipos ───────────────────────────────────────────────────────────────────

interface CalendarEvent extends Event {
    title: string;
    start: Date;
    end: Date;
    resource?: EventoCalendario;
}

// ─── Componente ──────────────────────────────────────────────────────────────

const CalendarioPage = () => {
    const [eventos, setEventos] = useState<EventoCalendario[]>([]);
    const [_tipos, setTipos] = useState<TipoEvento[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);

    // ── Carga de datos ───────────────────────────────────────────────────────

    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const [eventosData, tiposData] = await Promise.all([
                getEventos(),
                getTiposEvento(),
            ]);
            setEventos(eventosData);
            setTipos(tiposData);
        } catch (error) {
            const msg =
                error instanceof Error ? error.message : 'Error al cargar datos del calendario';
            toast.error(msg);
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // ── Mapeo a eventos del calendario ───────────────────────────────────────

    const calendarEvents: CalendarEvent[] = eventos.map((ev) => ({
        title: ev.titulo,
        start: new Date(ev.fecha_inicio),
        end: new Date(ev.fecha_fin),
        resource: ev,
    }));

    // ── Estilos por tipo ─────────────────────────────────────────────────────

    const eventPropGetter = useCallback(
        (event: CalendarEvent) => {
            const color = event.resource?.tipo_detalle?.color || '#3B82F6';
            return {
                style: {
                    backgroundColor: color,
                    borderColor: color,
                    borderRadius: '4px',
                    color: '#fff',
                    fontSize: '0.8rem',
                    border: 'none',
                },
            };
        },
        []
    );

    // ── Handlers ─────────────────────────────────────────────────────────────

    const handleSelectEvent = useCallback((event: CalendarEvent) => {
        setSelectedEvent(event);
    }, []);

    const handleCloseModal = useCallback(() => {
        setSelectedEvent(null);
    }, []);

    // ── Formateo de fecha legible ────────────────────────────────────────────

    const formatDateTime = (date: Date): string => {
        return format(date, "d 'de' MMMM 'de' yyyy, HH:mm", { locale: es });
    };

    // ── Render ───────────────────────────────────────────────────────────────

    return (
        <main className="bg-surface-container-lowest w-full flex flex-col gap-y-6 p-4 rounded-xl">
            {/* Encabezado */}
            <section className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                    <h2 className="font-black text-2xl text-on-surface tracking-tight md:text-3xl">
                        Calendario
                        <span className="text-text-primary pl-2">de Eventos</span>
                    </h2>
                    <p className="mt-1 text-secondary">
                        Gestione y visualice los eventos de su gimnasio.
                    </p>
                </div>
                <button
                    onClick={() => {
                        // PR 3: Abrir EventoForm para crear nuevo evento
                        toast('Formulario de creación disponible en la próxima actualización', {
                            icon: '📋',
                        });
                    }}
                    className="bg-sky-600 cursor-pointer flex font-semibold gap-2 items-center px-5 py-2.5 rounded-lg text-sm text-white transition-colors hover:bg-sky-500"
                >
                    + Nuevo Evento
                </button>
            </section>

            {/* Calendario */}
            {isLoading ? (
                <div className="text-center py-12 text-secondary">Cargando eventos...</div>
            ) : (
                <section className="bg-surface-container-high rounded-xl p-4">
                    <Calendar
                        localizer={localizer}
                        events={calendarEvents}
                        startAccessor="start"
                        endAccessor="end"
                        style={{ height: 650 }}
                        views={['month', 'week', 'day', 'agenda']}
                        defaultView="month"
                        messages={{
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
                            noEventsInRange: 'No hay eventos en este rango',
                            showMore: (count: number) => `+${count} más`,
                        }}
                        eventPropGetter={eventPropGetter}
                        onSelectEvent={handleSelectEvent}
                        popup
                        selectable
                    />
                </section>
            )}

            {/* Modal de detalle del evento */}
            {selectedEvent && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                    <div className="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-lg mx-4 p-6 relative">
                        {/* Header */}
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-bold text-on-surface">
                                {selectedEvent.title}
                            </h3>
                            <button
                                onClick={handleCloseModal}
                                className="text-secondary cursor-pointer hover:text-on-surface transition-colors"
                            >
                                <IoClose size={24} />
                            </button>
                        </div>

                        {/* Color indicator + tipo */}
                        {selectedEvent.resource?.tipo_detalle && (
                            <div className="flex items-center gap-2 mb-3">
                                <span
                                    className="inline-block w-4 h-4 rounded-full"
                                    style={{
                                        backgroundColor:
                                            selectedEvent.resource.tipo_detalle.color,
                                    }}
                                />
                                <span className="text-sm font-medium text-secondary">
                                    {selectedEvent.resource.tipo_detalle.nombre}
                                </span>
                            </div>
                        )}

                        {/* Descripción */}
                        {selectedEvent.resource?.descripcion && (
                            <p className="text-on-surface mb-4">
                                {selectedEvent.resource.descripcion}
                            </p>
                        )}

                        {/* Fechas */}
                        <div className="space-y-2 text-sm text-secondary">
                            <p>
                                <span className="font-semibold text-on-surface">Inicio:</span>{' '}
                                {formatDateTime(selectedEvent.start)}
                            </p>
                            <p>
                                <span className="font-semibold text-on-surface">Fin:</span>{' '}
                                {formatDateTime(selectedEvent.end)}
                            </p>
                        </div>

                        {/* Actions placeholder (PR 3) */}
                        <div className="flex gap-3 mt-6 pt-4 border-t border-surface-container-high">
                            <button
                                onClick={() => {
                                    toast(
                                        'Editar evento disponible en la próxima actualización',
                                        { icon: '📋' }
                                    );
                                }}
                                className="flex-1 bg-sky-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-sky-500"
                            >
                                Editar
                            </button>
                            <button
                                onClick={() => {
                                    toast(
                                        'Eliminar evento disponible en la próxima actualización',
                                        { icon: '📋' }
                                    );
                                }}
                                className="flex-1 bg-red-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-red-500"
                            >
                                Eliminar
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </main>
    );
};
export default CalendarioPage;