import os
import logging
from django.apps import AppConfig

logger = logging.getLogger(__name__)


class GimnasioappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'gimnasioApp'

    def ready(self):
        import sys

        # Importar señales para seed de membresías por defecto (siempre)
        import gimnasioApp.signals  # noqa: F401

        # Avoid running demo admin creation during management commands or pytest
        if len(sys.argv) >= 2 and sys.argv[1] in ['migrate', 'makemigrations', 'collectstatic', 'test']:
            return
        if os.environ.get('PYTEST_CURRENT_TEST'):
            return

        self._create_demo_admin()

    def _create_demo_admin(self):
        """
        Creates a demo admin user for portfolio/recruitment.
        Uses environment variables for credentials.
        """
        from .models import Usuario, Gimnasio
        from django.db.utils import OperationalError
        
        # Check if admin already exists
        try:
            if Usuario.objects.filter(roles='admin').exists():
                logger.info("Admin user already exists, skipping creation.")
                return
        except OperationalError:
            # Tables don't exist yet (e.g., during pytest collection before migrations)
            logger.info("Database tables not ready, skipping demo admin creation.")
            return
        
        try:
            # FIRST: Create or get Gimnasio (tenant)
            gimnasio, created = Gimnasio.objects.get_or_create(
                name=os.environ.get('DEMO_GIMNASIO_NAME', 'Gimnasio Principal'),
                defaults={
                    'address': 'Dirección Demo',
                    'phone': '123456789',
                    'is_active': True
                }
            )
            if created:
                logger.info(f"✅ Created demo gimnasio: {gimnasio.name}")
            
            # Get credentials from environment variables (use defaults if not set)
            admin_email = os.environ.get('DEMO_ADMIN_EMAIL', 'admin@gimnasio.com')
            admin_password = os.environ.get('DEMO_ADMIN_PASSWORD', 'admin123')
            admin_name = os.environ.get('DEMO_ADMIN_NAME', 'Admin')
            admin_lastname = os.environ.get('DEMO_ADMIN_LASTNAME', 'Demo')
            
            # Create admin user ASSOCIATED with the gimnasio
            Usuario.objects.create_user(
                email=admin_email,
                password=admin_password,
                name=admin_name,
                lastname=admin_lastname,
                roles='admin',
                gimnasio=gimnasio  # <-- IMPORTANT: Associate with gimnasio
            )
            logger.info(f"✅ Created demo admin user: {admin_email}")
        
        except Exception as e:
            logger.error(f"❌ Error creating demo admin: {e}", exc_info=True)