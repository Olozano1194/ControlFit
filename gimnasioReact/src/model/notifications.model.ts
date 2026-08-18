// ─── Notificaciones (Nivel 1) ─────────────────────────────────────────────────
// Contrato del API persistente de notificaciones: la lista devuelve SOLO las
// no leídas del gimnasio (las leídas desaparecen), ordenadas de más reciente
// a más antigua. Cada fila tiene id propio para claves estables en React.

export interface Notification {
    id: number;
    tipo: 'por_vencer' | 'vencida' | 'evento';
    titulo: string;
    mensaje: string;
    fecha: string;
    relacion_tipo: string;
    relacion_id: number | null;
    link: string;
    whatsapp_link: string | null;
    is_read: boolean;
    read_at: string | null;
    created_at: string;
}

// Respuesta de GET /Notificaciones/no-leidas/ — conteo para el badge del menú.
export interface UnreadCountResponse {
    count: number;
}