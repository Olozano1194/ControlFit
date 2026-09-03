"""
Email service for ControlFit.
Handles sending welcome emails to new gym admins via Resend HTTP API.
"""

import requests
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

RESEND_API_URL = "https://api.resend.com/emails"


def send_welcome_email(gym_id: int, admin_id: int, temp_password: str) -> None:
    """
    Envía email de bienvenida al admin del nuevo gym via Resend HTTP API.
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

    # Resend HTTP API
    api_key = getattr(settings, 'RESEND_API_KEY', None)
    if not api_key:
        logger.error("RESEND_API_KEY not configured in settings")
        return

    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'ControlFit <onboarding@resend.dev>')

    payload = {
        "from": from_email,
        "to": [admin.email],
        "subject": subject,
        "html": html_message,
        "text": plain_message,
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(RESEND_API_URL, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        logger.info("Welcome email sent to %s for gym %s via Resend API", admin.email, gym.name)
    except requests.exceptions.RequestException as e:
        logger.exception("Failed to send welcome email to %s via Resend API: %s", admin.email, e)
        # NO re-raise — fire-and-forget per design