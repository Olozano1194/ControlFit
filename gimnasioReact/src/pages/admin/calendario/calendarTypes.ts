import { Event } from 'react-big-calendar';
import { EventoCalendario } from '../../../model/calendario.model';

// ─── Tipos ───────────────────────────────────────────────────────────────────

export interface CalendarEvent extends Event {
    title: string;
    start: Date;
    end: Date;
    resource?: EventoCalendario;
}

// Convierte un EventoCalendario del API al formato interno del calendario.
// Se reutiliza para el listado y para el deep link (?evento=<id>) de
// notificaciones: el evento puede no estar en el rango inicial cargado.
export const toCalendarEvent = (ev: EventoCalendario): CalendarEvent => ({
    title: ev.titulo,
    start: new Date(ev.fecha_inicio),
    end: new Date(ev.fecha_fin),
    resource: ev,
});