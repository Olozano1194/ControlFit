import { useState, useEffect } from "react";
import React from "react";
//icons
import { RiCloseLine, RiInformationLine, RiCheckLine, RiInboxLine } from 'react-icons/ri';
import { IoMdNotifications } from "react-icons/io";
import { FaWhatsapp } from "react-icons/fa6";
//Enlaces
import { Link } from "react-router-dom";
//react-menu
import { Menu, MenuButton, MenuItem, MenuItems } from '@headlessui/react';
//Notificaciones
import { getNotifications, getUnreadCount, markOneRead, markAllAsRead } from "../../api/action/notifications.api";
//Models
import { Notification } from "../../model/notifications.model";


const NotificationMenu = () => {
    //notificaciones
    const [notifications, setNotifications] = useState<Notification[]>([]);
    const [count, setCount] = useState(0);

    useEffect(() => {
        const fetchNotifications = async () => {
            try {
                // El badge usa el conteo real del backend (no la longitud de la lista)
                const [data, unread] = await Promise.all([
                    getNotifications(),
                    getUnreadCount(),
                ]);
                setNotifications(data);
                setCount(unread.count);
            } catch (error) {
                console.error('Error al cargar notificaciones:', error);
            }
        };
        fetchNotifications();

        //Actualizar cada 5 minutos
        const intervalId = setInterval(fetchNotifications, 5 * 60 * 1000);
        return () => clearInterval(intervalId);
    }, []);

    //Marcar una notificación como leída y quitarla de la lista (el badge baja)
    const handleMarkOneRead = async (id: number) => {
        try {
            await markOneRead(id);
            setNotifications((prev) => prev.filter((n) => n.id !== id));
            setCount((prev) => Math.max(0, prev - 1));
        } catch (error) {
            console.error('Error al marcar como leída:', error);
        }
    };

    //Marcar todas como leídas (llama al backend para persistir)
    const handleMarkAllAsRead = async () => {
        try {
            await markAllAsRead();
            setNotifications([]);
            setCount(0);
        } catch (error) {
            console.error('Error al marcar como leídas:', error);
        }
    };

    //Obtener icono según el tipo de notificación
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
        <Menu>
            <MenuButton className="border-r border-nav/30 cursor-pointer text-nav relative hover:text-title p-2 transition-colors">
                <IoMdNotifications className="text-2xl" />
                {count > 0 && (
                    <span className="absolute -top-0.5 right-0 bg-primary py-0.5 px-1.25 box-content text-surface-container-high rounded-full text-[8px] font-bold">
                        {count}
                    </span>
                )}
            </MenuButton>
            <MenuItems anchor='bottom end' className='bg-surface-container-lowest mt-1 p-4 rounded-lg max-h-[70vh] overflow-y-auto w-96'>
                <div className="flex justify-between items-center mb-2">
                    <h1 className="text-title font-medium">Notificaciones</h1>
                    {count > 0 && (
                        <button
                            onClick={handleMarkAllAsRead}
                            className="text-sm text-primary hover:underline"
                        >
                            Marcar como leídas
                        </button>
                    )}
                </div>
                <hr className="my-3 border-nav/30" />
                {notifications.length === 0 ? (
                    <div className="text-center py-4">
                        <RiInboxLine className="mx-auto text-3xl text-nav/30 mb-2" />
                        <p className="text-nav">No hay notificaciones nuevas</p>
                    </div>
                ) : (
                    notifications.map((notification, index) => (
                        <React.Fragment key={notification.id}>
                            <MenuItem as='div' className='p-0 hover:bg-slate-100'>
                                <div className="flex flex-col">
                                    <Link
                                        to={notification.link}
                                        onClick={() => handleMarkOneRead(notification.id)}
                                        className="flex flex-1 items-start gap-x-3 py-2 px-4 hover:bg-slate-100 transition-colors rounded-lg text-dark"
                                    >
                                        {getNotificationIcon(notification.tipo)}
                                        <div className="text-sm flex-1">
                                            <div className="flex items-start justify-between gap-2">
                                                <span className="font-medium">{notification.titulo}</span>
                                                <span className="text-xs text-nav">{notification.fecha}</span>
                                            </div>
                                            <p className="text-dark mt-1">{notification.mensaje}</p>
                                        </div>
                                    </Link>
                                    
                                    {/* Botón de WhatsApp (no dispara la lectura) */}
                                    {notification.whatsapp_link && (
                                        <a
                                            href={notification.whatsapp_link}
                                            target="_blank"
                                            rel="noopener noreferrer"
                                            className="flex items-center gap-2 mx-4 mb-2 py-2 px-4 bg-green-500 hover:bg-green-600 text-white rounded-lg text-sm font-medium transition-colors"
                                        >
                                            <FaWhatsapp className="text-lg" />
                                            Enviar mensaje por WhatsApp
                                        </a>
                                    )}
                                </div>
                            </MenuItem>
                            {index < notifications.length - 1 && <hr className="my-3 border-nav" />}
                        </React.Fragment>
                    ))
                )}
                <hr className="my-3 border-nav/30" />
                <MenuItem as='div' className='p-0 hover:bg-slate-100 flex justify-center cursor-default rounded-xl'>
                    <Link
                        to="/dashboard/notifications"
                        className="text-title text-sm hover:text-nav/80 transition-colors font-medium"
                    >
                        Ver todas las notificaciones
                    </Link>
                </MenuItem>
            </MenuItems>
        </Menu>
    );
}
export default NotificationMenu;