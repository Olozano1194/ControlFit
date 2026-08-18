import { Notification, UnreadCountResponse } from "../../model/notifications.model"
import { axiosPrivate } from "../axios/axios.private";

// Lista de notificaciones NO leídas del gimnasio.
// El backend genera de forma perezosa e idempotente (vencimientos y eventos
// del día) y devuelve solo las no leídas, ordenadas por -created_at.
export const getNotifications = async (): Promise<Notification[]> => {
    const response = await axiosPrivate.get<Notification[]>('/Notificaciones/')
    return response.data;
}

// Conteo de notificaciones no leídas para el badge del menú.
export const getUnreadCount = async (): Promise<UnreadCountResponse> => {
    const response = await axiosPrivate.get<UnreadCountResponse>('/Notificaciones/no-leidas/')
    return response.data;
}

// Marca una notificación como leída (is_read=True). Al recargar la lista,
// la notificación ya no aparece (la lista solo muestra no leídas).
export const markOneRead = async (id: number): Promise<void> => {
    await axiosPrivate.post(`/Notificaciones/${id}/marcar-leida/`)
}

// Marca todas las notificaciones no leídas del gimnasio como leídas.
export const markAllAsRead = async (): Promise<void> => {
    await axiosPrivate.post('/Notificaciones/marcar-todas-leidas/')
}