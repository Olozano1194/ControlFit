import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { toast } from 'react-hot-toast';
// Icons
import { RiCloseLine, RiInformationLine, RiCheckLine, RiInboxLine, RiArrowLeftLine } from 'react-icons/ri';
import { FaWhatsapp } from "react-icons/fa6";
// Notifications API
import { getNotifications, markOneRead, markAllAsRead } from "../../../api/action/notifications.api";
import { Notification } from "../../../model/notifications.model";

const NotificationsPage = () => {
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [loading, setLoading] = useState(true);
    const navigate = useNavigate();

    useEffect(() => {
        const fetchNotifications = async () => {
            setLoading(true);
            try {
                const data = await getNotifications();
                setNotifications(data);
            } catch (error) {
                toast.error(error instanceof Error ? error.message : 'Error al cargar notificaciones');
            } finally {
                setLoading(false);
            }
        };
        fetchNotifications();
    }, []);

    const handleMarkOneRead = async (id: number) => {
        try {
            await markOneRead(id);
            setNotifications((prev) => prev.filter((n) => n.id !== id));
        } catch (error) {
            toast.error(error instanceof Error ? error.message : 'Error al marcar como leída');
        }
    };

    const handleMarkAllAsRead = async () => {
        try {
            await markAllAsRead();
            setNotifications([]);
            toast.success('Todas las notificaciones fueron marcadas como leídas');
        } catch (error) {
            toast.error(error instanceof Error ? error.message : 'Error al marcar como leídas');
        }
    };

    // Icono según tipo
    const getNotificationIcon = (tipo: Notification['tipo']) => {
        switch (tipo) {
            case 'por_vencer':
                return <RiInformationLine className="p-2 bg-yellow-100 text-yellow-500 box-content rounded-full" />;
            case 'vencida':
                return <RiCloseLine className="p-2 bg-red-100 text-red-500 box-content rounded-full" />;
            case 'evento':
                return <RiCheckLine className="p-2 bg-green-100 text-green-500 box-content rounded-full" />;
            default:
                return <RiInformationLine className="p-2 bg-blue-100 text-blue-500 box-content rounded-full" />;
        }
    };

    return (
        <div className="p-6 max-w-3xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-4">
                    <button
                        onClick={() => navigate(-1)}
                        className="p-2 hover:bg-slate-100 rounded-lg transition-colors"
                    >
                        <RiArrowLeftLine className="text-2xl text-title" />
                    </button>
                    <h1 className="text-2xl font-bold text-title">Notificaciones</h1>
                </div>
                {notifications.length > 0 && (
                    <button
                        onClick={handleMarkAllAsRead}
                        className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary/90 transition-colors text-sm font-medium"
                    >
                        Marcar todas como leídas
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="bg-surface-container-lowest rounded-xl shadow-sm overflow-hidden">
                {loading ? (
                    <div className="p-8 text-center">
                        <div className="animate-pulse text-nav">Cargando notificaciones...</div>
                    </div>
                ) : notifications.length === 0 ? (
                    <div className="p-12 text-center">
                        <RiInboxLine className="mx-auto text-6xl text-nav/30 mb-4" />
                        <p className="text-lg text-nav font-medium">No hay notificaciones</p>
                        <p className="text-sm text-nav/60 mt-1">
                            Las notificaciones aparecerán aquí cuando alguna membresía esté próxima a vencer o haya vencido.
                        </p>
                    </div>
                ) : (
                    <div className="divide-y divide-nav/10">
                        {notifications.map((notification) => (
                            <div key={notification.id} className="p-4 hover:bg-slate-50 transition-colors">
                                <div className="flex items-start gap-3">
                                    <Link
                                        to={notification.link}
                                        className="flex gap-4 flex-1 min-w-0"
                                    >
                                        {/* Icon */}
                                        <div className="shrink-0 mt-1">
                                            {getNotificationIcon(notification.tipo)}
                                        </div>

                                        {/* Content */}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-start justify-between gap-2">
                                                <span className="font-semibold text-title">{notification.titulo}</span>
                                                <span className="text-xs text-nav whitespace-nowrap">{notification.fecha}</span>
                                            </div>
                                            <p className="text-sm text-dark mt-1">{notification.mensaje}</p>

                                            {/* WhatsApp button (no dispara la lectura) */}
                                            {notification.whatsapp_link && (
                                                <a
                                                    href={notification.whatsapp_link}
                                                    target="_blank"
                                                    rel="noopener noreferrer"
                                                    onClick={(e) => e.stopPropagation()}
                                                    className="inline-flex items-center gap-2 mt-3 py-2 px-4 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors"
                                                >
                                                    <FaWhatsapp className="text-lg" />
                                                    Enviar mensaje por WhatsApp
                                                </a>
                                            )}
                                        </div>
                                    </Link>

                                    {/* Botón de lectura individual */}
                                    <button
                                        onClick={() => handleMarkOneRead(notification.id)}
                                        className="shrink-0 mt-1 px-3 py-1.5 bg-primary/10 text-primary rounded-lg hover:bg-primary/20 transition-colors text-xs font-medium"
                                    >
                                        Marcar como leída
                                    </button>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};
export default NotificationsPage;