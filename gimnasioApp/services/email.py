"""
Email service for ControlFit.
Handles sending welcome emails to new gym admins.
"""

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def send_welcome_email(gym_id: int, admin_id: int, temp_password: str) -> None:
    """
    Envía email de bienvenida al admin del nuevo gym.
    Síncrono, usa settings.EMAIL_BACKEND.
    NO lanza excepción — loguea error y retorna (fire-and-forget).
    """
    from gimnasioApp.models import Gimnasio, Usuario

    try:
        gym = Gimnasio.objects.select_related().get(pk=gym_id)
        admin = Usuario.objects.select_related('gimnasio').get(pk=admin_id)
    except (Gimnasio.DoesNotExist, Usuario.DoesNotExist) as e:
        logger.error("Welcome email: gym %s or admin %s not found", gym_id, admin_id)
        return

    context = {
        'gym_name': gym.name,
        'admin_email': admin.email,
        'temp_password': temp_password,
        'login_url': f"{settings.FRONTEND_URL}/login",
        'support_email': getattr(settings, 'SUPPORT_EMAIL', 'soporte@controlfit.app'),
    }

    subject = f"Bienvenido a ControlFit 🎉 Tu gimnasio {gym.name} está listo"

    # Render templates
    html_message = render_to_string('emails/welcome_admin.html', context)
    plain_message = render_to_string('emails/welcome_admin.txt', context)

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[admin.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info("Welcome email sent to %s for gym %s", admin.email, gym.name)
    except Exception as e:
        logger.exception("Failed to send welcome email to %s: %s", admin.email, e)
        # NO re-raise — fire-and-forget per design