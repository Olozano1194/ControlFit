import { EventoCalendario } from '../../../../model/calendario.model';

// ─── Props ───────────────────────────────────────────────────────────────────

export interface EventoFormProps {
    isOpen: boolean;
    onClose: () => void;
    event?: EventoCalendario | null;
    onSuccess: () => void;
    initialDates?: { start: string; end: string };
}

export interface FormData {
    titulo: string;
    fecha_inicio: string;
    fecha_fin: string;
    descripcion: string;
    tipo: string;
    relacion_tipo: string;
    relacion_id: string;
}