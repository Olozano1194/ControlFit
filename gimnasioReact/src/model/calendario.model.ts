// ─── TipoEvento ──────────────────────────────────────────────────────────────
export interface TipoEvento {
    id: number;
    nombre: string;
    color: string;
    gimnasio: number;
    created_at: string;
}

export interface TipoEventoSimple {
    id: number;
    nombre: string;
    color: string;
}

export interface CreateTipoEventoDto {
    nombre: string;
    color: string;
}

export type UpdateTipoEventoDto = Partial<CreateTipoEventoDto>;

// ─── EventoCalendario ────────────────────────────────────────────────────────
export interface EventoCalendario {
    id: number;
    titulo: string;
    fecha_inicio: string;
    fecha_fin: string;
    descripcion: string;
    tipo: number | null;
    tipo_detalle: TipoEventoSimple | null;
    relacion_tipo: string;
    relacion_id: number | null;
    created_by: number | null;
    gimnasio: number;
    created_at: string;
}

export interface CreateEventoDto {
    titulo: string;
    fecha_inicio: string;
    fecha_fin: string;
    descripcion?: string;
    tipo?: number | null;
    relacion_tipo?: string;
    relacion_id?: number | null;
}

export type UpdateEventoDto = Partial<CreateEventoDto>;