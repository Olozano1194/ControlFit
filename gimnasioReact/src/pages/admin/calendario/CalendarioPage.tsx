import { useCallback, useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { type SlotInfo } from 'react-big-calendar';
import {
    type EventInteractionArgs,
} from 'react-big-calendar/lib/addons/dragAndDrop';
import { format } from 'date-fns';
import { es } from 'date-fns/locale/es';
import { toast } from 'react-hot-toast';
import { IoClose } from 'react-icons/io5';
import {
    getEventos,
    getEvento,
    patchEvento,
    deleteEvento,
} from '../../../api/action/calendario.api';
import { EventoCalendario } from '../../../model/calendario.model';
import { useAuth } from '../../../context/useAuth';
import { getApiErrorMessage } from '../../../utils/apiError';
import EventoForm from './EventoForm';
import TipoEventoAdmin from './TipoEventoAdmin';
import { toApiISO, toLocalInputValue, normalizeSlotEnd } from './dateTime';
import 'react-big-calendar/lib/css/react-big-calendar.css';
import 'react-big-calendar/lib/addons/dragAndDrop/styles.css';
import { CalendarEvent } from './calendarTypes';
import { toCalendarEvent } from './calendarTypes';
import CalendarView from './CalendarView';



// ─── Componente ──────────────────────────────────────────────────────────────

const CalendarioPage = () => {
    const { user } = useAuth();
    const isAdmin = user?.roles?.includes('admin') ?? false;

    const [eventos, setEventos] = useState<EventoCalendario[]>([]);
    const [isLoading, setIsLoading] = useState(false);
    const [selectedEvent, setSelectedEvent] = useState<CalendarEvent | null>(null);
    const [isEventoFormOpen, setIsEventoFormOpen] = useState(false);
    const [editingEvent, setEditingEvent] = useState<EventoCalendario | null>(null);
    const [isTipoAdminOpen, setIsTipoAdminOpen] = useState(false);
    const [slotPrefill, setSlotPrefill] = useState<{ start: Date; end: Date } | null>(
        null
    );    

    // ── Carga de datos ───────────────────────────────────────────────────────
    // Los tipos de evento los consume EventoForm al abrirse; acá solo se
    // necesitan los eventos para pintar el calendario.
    const fetchData = useCallback(async () => {
        setIsLoading(true);
        try {
            const eventosData = await getEventos();
            setEventos(eventosData);
        } catch (error) {
            toast.error(
                getApiErrorMessage(error, 'Error al cargar datos del calendario')
            );
        } finally {
            setIsLoading(false);
        }
    }, []);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    // ── Deep link desde notificaciones (?evento=<id>) ────────────────────────
    const [searchParams] = useSearchParams();

    useEffect(() => {
        const eventoParam = searchParams.get('evento');
        if (!eventoParam) return;
        const eventoId = Number(eventoParam);
        if (Number.isNaN(eventoId)) return;
        // Abre el modal de detalle con el evento traído por id, aunque no esté
        // dentro del rango inicial del calendario.
        getEvento(eventoId)
            .then((ev) => setSelectedEvent(toCalendarEvent(ev)))
            .catch(() => toast.error('No se encontró el evento solicitado'));
    }, [searchParams]);

    // ── Mapeo a eventos del calendario ───────────────────────────────────────

    const calendarEvents: CalendarEvent[] = eventos.map(toCalendarEvent);   

    // ── Handlers ─────────────────────────────────────────────────────────────

    const handleSelectEvent = useCallback((event: CalendarEvent) => {
        setSelectedEvent(event);
    }, []);

    const handleCloseModal = useCallback(() => {
        setSelectedEvent(null);
    }, []);

    const handleSelectSlot = useCallback((slotInfo: SlotInfo) => {
        setSlotPrefill({
            start: slotInfo.start,
            end: normalizeSlotEnd(slotInfo.end),
        });
        setEditingEvent(null);
        setIsEventoFormOpen(true);
    }, []);

    const handleEventFormSuccess = useCallback(() => {
        fetchData();
    }, [fetchData]);

    // ── Drag & Drop (admin) ──────────────────────────────────────────────────

    const handleEventDrop = useCallback(
        async ({ start, end, event }: EventInteractionArgs<CalendarEvent>) => {
            if (!event.resource?.id) return;
            try {
                await patchEvento(event.resource.id, {
                    fecha_inicio: toApiISO(new Date(start)),
                    fecha_fin: toApiISO(new Date(end)),
                });
                toast.success('Evento actualizado correctamente');
                fetchData();
            } catch (error) {
                toast.error(getApiErrorMessage(error, 'Error al mover el evento'));
            }
        },
        [fetchData]
    );

    const handleEventResize = handleEventDrop;

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
                <div className="flex flex-wrap gap-3">
                    {isAdmin && (
                        <button
                            onClick={() => setIsTipoAdminOpen(true)}
                            className="bg-surface-container-high cursor-pointer font-semibold px-5 py-2.5 rounded-lg text-sm text-on-surface transition-colors hover:bg-surface-container-high/80"
                        >
                            Gestionar Tipos
                        </button>
                    )}
                    <button
                        onClick={() => {
                            setEditingEvent(null);
                            setSlotPrefill(null);
                            setIsEventoFormOpen(true);
                        }}
                        className="bg-sky-600 cursor-pointer flex font-semibold gap-2 items-center px-5 py-2.5 rounded-lg text-sm text-white transition-colors hover:bg-sky-500"
                    >
                        + Nuevo Evento
                    </button>
                </div>
            </section>

            {/* Calendario */}
            {isLoading ? (
                <div className="text-center py-12 text-secondary">Cargando eventos...</div>
            ) : (
                <section className="bg-surface-container-high rounded-xl p-4">
                    <CalendarView
                        isAdmin={isAdmin}
                        events={calendarEvents}
                        onSelectEvent={handleSelectEvent}
                        onSelectSlot={handleSelectSlot}
                        onEventDrop={handleEventDrop}
                        onEventResize={handleEventResize}   
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

                        {/* Acciones */}
                        <div className="flex gap-3 mt-6 pt-4 border-t border-surface-container-high">
                            <button
                                onClick={() => {
                                    setEditingEvent(selectedEvent?.resource ?? null);
                                    setSelectedEvent(null);
                                    setIsEventoFormOpen(true);
                                }}
                                className="flex-1 bg-sky-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-sky-500"
                            >
                                Editar
                            </button>
                            {isAdmin && (
                                <button
                                    onClick={() => {
                                        const eventId = selectedEvent.resource?.id;
                                        if (!eventId) return;
                                        if (!window.confirm('¿Eliminar este evento?')) return;
                                        deleteEvento(eventId)
                                            .then(() => {
                                                toast.success('Evento eliminado correctamente');
                                                setSelectedEvent(null);
                                                fetchData();
                                            })
                                            .catch((err) =>
                                                toast.error(
                                                    getApiErrorMessage(
                                                        err,
                                                        'Error al eliminar'
                                                    )
                                                )
                                            );
                                    }}
                                    className="flex-1 bg-red-600 cursor-pointer font-semibold px-4 py-2 rounded-lg text-sm text-white transition-colors hover:bg-red-500"
                                >
                                    Eliminar
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Modal de creación/edición de evento */}
            <EventoForm
                isOpen={isEventoFormOpen}
                onClose={() => setIsEventoFormOpen(false)}
                event={editingEvent}
                onSuccess={handleEventFormSuccess}
                initialDates={
                    slotPrefill
                        ? {
                              start: toLocalInputValue(slotPrefill.start),
                              end: toLocalInputValue(slotPrefill.end),
                          }
                        : undefined
                }
            />

            {/* Modal de gestión de tipos (admin) */}
            {isTipoAdminOpen && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm">
                    <div className="bg-surface-container-lowest rounded-xl shadow-2xl w-full max-w-2xl mx-4 p-6 relative max-h-[90vh] overflow-y-auto">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-xl font-bold text-on-surface">
                                Gestión de Tipos de Evento
                            </h3>
                            <button
                                onClick={() => setIsTipoAdminOpen(false)}
                                className="text-secondary cursor-pointer hover:text-on-surface transition-colors"
                                aria-label="Cerrar"
                            >
                                <IoClose size={24} />
                            </button>
                        </div>
                        <TipoEventoAdmin onSuccess={fetchData} />
                    </div>
                </div>
            )}
        </main>
    );
};
export default CalendarioPage;