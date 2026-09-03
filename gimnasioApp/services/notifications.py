"""Generación perezosa e idempotente de notificaciones para el staff.

Fuentes (Nivel 1):
- Membresías asignadas que expiran dentro de los próximos 3 días (excluyendo hoy).
- Membresías asignadas ya vencidas (dateFinal <= hoy).
- Eventos de calendario cuyo fecha_inicio cae en la fecha de hoy (UTC, date.today()).

La idempotencia se garantiza con get_or_create sobre la UniqueConstraint
(gimnasio, relacion_tipo, relacion_id, tipo) del modelo Notification.
"""

from datetime import date, timedelta

from ..models import EventoCalendario, MembresiaAsignada, Notification

# Links del frontend (rutas existentes en el SPA)
LINK_MEMBRESIAS = '/dashboard/asignar-membresia-list'
LINK_CALENDARIO = '/dashboard/calendar'

# Prefijo de país hardcodeado para WhatsApp (Colombia). Se preserva del
# comportamiento legacy; parametrizarlo queda para un cambio futuro.
PREFIJO_WHATSAPP = '57'


class NotificationManager:
    """Genera (o reutiliza) las notificaciones pendientes de un gimnasio."""

    @classmethod
    def generate_for_gimnasio(cls, gimnasio):
        """Crea las notificaciones faltantes para el gimnasio dado, sin duplicar.

        Es idempotente: si la notificación ya existe (misma clave de unicidad),
        get_or_create devuelve la fila existente y no crea una nueva.
        """
        # Superadmin no tiene gimnasio asignado -> no hay notificaciones que generar
        if gimnasio is None:
            return

        today = date.today()
        three_day_later = today + timedelta(days=3)

        # Membresías próximas a vencer: (hoy, hoy+3]
        expiring_memberships = MembresiaAsignada.objects.filter(
            miembro__gimnasio=gimnasio,
            dateFinal__gt=today,
            dateFinal__lte=three_day_later,
        ).select_related('miembro', 'membresia')
        for membership in expiring_memberships:
            cls._crear_membresia(gimnasio, membership, 'por_vencer', today)

        # Membresías vencidas: dateFinal <= hoy
        expired_memberships = MembresiaAsignada.objects.filter(
            miembro__gimnasio=gimnasio,
            dateFinal__lte=today,
        ).select_related('miembro', 'membresia')
        for membership in expired_memberships:
            cls._crear_membresia(gimnasio, membership, 'vencida', today)

        # Eventos del día: fecha_inicio con la misma fecha (UTC) que hoy
        eventos_hoy = EventoCalendario.objects.filter(
            gimnasio=gimnasio,
            fecha_inicio__date=today,
        )
        for evento in eventos_hoy:
            cls._crear_evento(evento)

    @classmethod
    def _crear_membresia(cls, gimnasio, membership, tipo, today):
        """Crea (o reutiliza) la notificación de membresía por vencer/vencida."""
        member_name = f"{membership.miembro.name} {membership.miembro.lastname}"
        membership_name = membership.membresia.name
        exp_date = membership.dateFinal.strftime('%d/%m/%Y')

        if tipo == 'por_vencer':
            days_left = (membership.dateFinal - today).days
            titulo = 'Membresía próxima a expirar'
            mensaje = (
                f'La membresía de {member_name} - {membership_name} '
                f'expirará en {days_left} días.'
            )
            wa_message = (
                f"Hola%20{member_name},%20tu%20membresía%20({membership_name})%20"
                f"expira%20el%20{exp_date}%20en%20{days_left}%20días.%20"
                "¿Deseas%20renovar%20ahora%20y%20seguir%20entrenando%20con%20nosotros%3F"
            )
        else:
            titulo = 'Membresía vencida'
            mensaje = (
                f'La membresía de {member_name} - {membership_name} ya venció.'
            )
            wa_message = (
                f"Hola%20{member_name},%20tu%20membresía%20({membership_name})%20"
                f"venció%20el%20{exp_date}.%20¡Te%20esperamos%20de%20vuelta%20"
                "para%20que%20renueves%20y%20continúes%20entrenando%21"
            )

        whatsapp_link = cls._construir_whatsapp_link(membership.miembro.phone, wa_message)

        Notification.objects.get_or_create(
            gimnasio=gimnasio,
            tipo=tipo,
            relacion_tipo='membership',
            relacion_id=membership.id,
            defaults={
                'titulo': titulo,
                'mensaje': mensaje,
                'fecha': membership.dateFinal,
                'link': LINK_MEMBRESIAS,
                'whatsapp_link': whatsapp_link,
            },
        )

    @classmethod
    def _crear_evento(cls, evento):
        """Crea (o reutiliza) la notificación de evento programado para hoy."""
        Notification.objects.get_or_create(
            gimnasio=evento.gimnasio,
            tipo='evento',
            relacion_tipo='evento',
            relacion_id=evento.id,
            defaults={
                'titulo': 'Evento programado hoy',
                'mensaje': f'El evento "{evento.titulo}" se realiza hoy.',
                'fecha': evento.fecha_inicio.date(),
                'link': f'{LINK_CALENDARIO}?evento={evento.id}',
                'whatsapp_link': None,
            },
        )

    @staticmethod
    def _construir_whatsapp_link(phone, wa_message):
        """Construye el enlace wa.me con prefijo 57; None si no hay teléfono."""
        phone_clean = ''.join(filter(str.isdigit, phone or ''))
        if phone_clean and not phone_clean.startswith(PREFIJO_WHATSAPP):
            phone_clean = PREFIJO_WHATSAPP + phone_clean
        return f"https://wa.me/{phone_clean}?text={wa_message}" if phone_clean else None