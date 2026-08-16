import axios from 'axios';
import { axiosPrivate } from '../axios/axios.private';
import {
    TipoEvento,
    CreateTipoEventoDto,
    UpdateTipoEventoDto,
    EventoCalendario,
    CreateEventoDto,
    UpdateEventoDto,
} from '../../model/calendario.model';

// ─── Tipos de Evento ─────────────────────────────────────────────────────────

export const getTiposEvento = async (): Promise<TipoEvento[]> => {
    const { data } = await axiosPrivate.get<TipoEvento[]>('/TiposEvento/');
    return data;
};

export const createTipoEvento = async (
    dto: CreateTipoEventoDto
): Promise<TipoEvento> => {
    const { data } = await axiosPrivate.post<TipoEvento>('/TiposEvento/', dto);
    return data;
};

export const updateTipoEvento = async (
    id: number,
    dto: UpdateTipoEventoDto
): Promise<TipoEvento> => {
    const { data } = await axiosPrivate.put<TipoEvento>(`/TiposEvento/${id}/`, dto);
    return data;
};

export const deleteTipoEvento = async (id: number): Promise<void> => {
    await axiosPrivate.delete(`/TiposEvento/${id}/`);
};

// ─── Eventos de Calendario ───────────────────────────────────────────────────

export const getEventos = async (params?: {
    start?: string;
    end?: string;
}): Promise<EventoCalendario[]> => {
    const { data } = await axiosPrivate.get<EventoCalendario[]>('/CalendarioEventos/', {
        params,
    });
    return data;
};

export const getEvento = async (id: number): Promise<EventoCalendario> => {
    const { data } = await axiosPrivate.get<EventoCalendario>(`/CalendarioEventos/${id}/`);
    return data;
};

export const createEvento = async (
    dto: CreateEventoDto
): Promise<EventoCalendario> => {
    const { data } = await axiosPrivate.post<EventoCalendario>(
        '/CalendarioEventos/',
        dto
    );
    return data;
};

export const updateEvento = async (
    id: number,
    dto: UpdateEventoDto
): Promise<EventoCalendario> => {
    const { data } = await axiosPrivate.put<EventoCalendario>(
        `/CalendarioEventos/${id}/`,
        dto
    );
    return data;
};

export const deleteEvento = async (id: number): Promise<void> => {
    await axiosPrivate.delete(`/CalendarioEventos/${id}/`);
};

// ─── Público ─────────────────────────────────────────────────────────────────
// El endpoint público NO está bajo /gym/api/v1, así que usamos el dominio base.

const getBaseDomain = (): string => {
    const fullUrl =
        import.meta.env.MODE === 'development'
            ? (import.meta.env.VITE_API_URL_DEV as string)
            : (import.meta.env.VITE_API_URL_PROD as string);
    return fullUrl.replace('/gym/api/v1', '');
};

export const getEventosPublicos = async (
    gimnasioId: number
): Promise<EventoCalendario[]> => {
    const { data } = await axios.get<EventoCalendario[]>(
        `${getBaseDomain()}/api/calendario/publico/${gimnasioId}/`
    );
    return data;
};