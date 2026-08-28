from django.core.management.base import BaseCommand
from django.db import transaction
from gimnasioApp.models import Usuario, Gimnasio
import os


class Command(BaseCommand):
    help = 'Crea usuario admin de produccion usando variables de entorno ADMIN_EMAIL y ADMIN_PASSWORD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la recreacion si ya existe un admin con ese email',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Leer credenciales de variables de entorno
        admin_email = os.environ.get('ADMIN_EMAIL')
        admin_password = os.environ.get('ADMIN_PASSWORD')
        admin_name = os.environ.get('ADMIN_NAME', 'Admin')
        admin_lastname = os.environ.get('ADMIN_LASTNAME', 'Production')
        gimnasio_name = os.environ.get('ADMIN_GIMNASIO_NAME', 'Gimnasio Principal')

        if not admin_email or not admin_password:
            self.stdout.write(
                self.style.ERROR(
                    '[ERROR] Faltan variables de entorno requeridas: ADMIN_EMAIL y ADMIN_PASSWORD'
                )
            )
            self.stdout.write('   Configura en Render: ADMIN_EMAIL=tu@email.com ADMIN_PASSWORD=tu_password')
            return

        # Validar formato de email basico
        if '@' not in admin_email:
            self.stdout.write(self.style.ERROR('[ERROR] ADMIN_EMAIL no tiene formato valido'))
            return

        # Validar fortaleza minima de contrasena
        if len(admin_password) < 8:
            self.stdout.write(self.style.ERROR('[ERROR] ADMIN_PASSWORD debe tener al menos 8 caracteres'))
            return

        with transaction.atomic():
            # 1. Crear u obtener el gimnasio
            gimnasio, created = Gimnasio.objects.get_or_create(
                name=gimnasio_name,
                defaults={
                    'address': os.environ.get('ADMIN_GIMNASIO_ADDRESS', ''),
                    'phone': os.environ.get('ADMIN_GIMNASIO_PHONE', ''),
                    'is_active': True,
                }
            )
            if created:
                self.stdout.write(self.style.SUCCESS('[OK] Gimnasio creado: %s' % gimnasio.name))
            else:
                self.stdout.write('[INFO] Gimnasio ya existe: %s' % gimnasio.name)

            # 2. Verificar si ya existe admin con ese email
            existing_admin = Usuario.objects.filter(email=admin_email).first()
            
            if existing_admin:
                if force:
                    self.stdout.write('[WARN] Admin ya existe (%s), forzando actualizacion...' % admin_email)
                    existing_admin.set_password(admin_password)
                    existing_admin.name = admin_name
                    existing_admin.lastname = admin_lastname
                    existing_admin.roles = 'admin'
                    existing_admin.gimnasio = gimnasio
                    existing_admin.is_active = True
                    existing_admin.must_change_password = False
                    existing_admin.save()
                    self.stdout.write(self.style.SUCCESS('[OK] Admin actualizado: %s' % admin_email))
                else:
                    self.stdout.write(
                        self.style.WARNING('[WARN] Admin ya existe: %s' % admin_email)
                    )
                    self.stdout.write('   Usa --force para actualizar credenciales')
                return

            # 3. Crear nuevo admin de produccion
            admin_user = Usuario.objects.create_user(
                email=admin_email,
                password=admin_password,
                name=admin_name,
                lastname=admin_lastname,
                roles='admin',
                gimnasio=gimnasio,
                must_change_password=False,
                is_active=True,
            )
            
            self.stdout.write(
                self.style.SUCCESS('[OK] Admin de produccion creado: %s' % admin_email)
            )
            self.stdout.write('   Gimnasio: %s' % gimnasio.name)
            self.stdout.write('   Nombre: %s %s' % (admin_name, admin_lastname))