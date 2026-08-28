from django.core.management.base import BaseCommand
from django.db import transaction
from gimnasioApp.models import Usuario
import os


class Command(BaseCommand):
    help = 'Crea superadmin de plataforma (sin gimnasio asignado) usando SUPERADMIN_EMAIL y SUPERADMIN_PASSWORD'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Fuerza la actualizacion si ya existe superadmin con ese email',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        # Leer credenciales de variables de entorno
        superadmin_email = os.environ.get('SUPERADMIN_EMAIL')
        superadmin_password = os.environ.get('SUPERADMIN_PASSWORD')
        superadmin_name = os.environ.get('SUPERADMIN_NAME', 'Super')
        superadmin_lastname = os.environ.get('SUPERADMIN_LASTNAME', 'Admin')

        if not superadmin_email or not superadmin_password:
            self.stdout.write(
                self.style.ERROR(
                    '[ERROR] Faltan variables de entorno requeridas: SUPERADMIN_EMAIL y SUPERADMIN_PASSWORD'
                )
            )
            self.stdout.write('   Configura en Render: SUPERADMIN_EMAIL=tu@email.com SUPERADMIN_PASSWORD=tu_password')
            self.stdout.write('   Variables actuales: SUPERADMIN_EMAIL=%s SUPERADMIN_PASSWORD=%s' % (
                'SET' if superadmin_email else 'MISSING',
                'SET' if superadmin_password else 'MISSING'
            ))
            import sys
            sys.exit(1)

        # Validar formato de email basico
        if '@' not in superadmin_email:
            self.stdout.write(self.style.ERROR('[ERROR] SUPERADMIN_EMAIL no tiene formato valido'))
            import sys
            sys.exit(1)

        # Validar fortaleza minima de contrasena
        if len(superadmin_password) < 8:
            self.stdout.write(self.style.ERROR('[ERROR] SUPERADMIN_PASSWORD debe tener al menos 8 caracteres'))
            import sys
            sys.exit(1)

        with transaction.atomic():
            # 1. Verificar si ya existe superadmin con ese email
            existing_superadmin = Usuario.objects.filter(email=superadmin_email).first()
            
            if existing_superadmin:
                if force:
                    self.stdout.write('[WARN] Superadmin ya existe (%s), forzando actualizacion...' % superadmin_email)
                    existing_superadmin.set_password(superadmin_password)
                    existing_superadmin.name = superadmin_name
                    existing_superadmin.lastname = superadmin_lastname
                    existing_superadmin.roles = 'superadmin'
                    existing_superadmin.gimnasio = None  # Sin gimnasio = superadmin global
                    existing_superadmin.is_active = True
                    existing_superadmin.must_change_password = False
                    existing_superadmin.save()
                    self.stdout.write(self.style.SUCCESS('[OK] Superadmin actualizado: %s' % superadmin_email))
                else:
                    self.stdout.write(
                        self.style.WARNING('[WARN] Superadmin ya existe: %s' % superadmin_email)
                    )
                    self.stdout.write('   Usa --force para actualizar credenciales')
                return

            # 2. Crear nuevo superadmin de plataforma (SIN gimnasio)
            superadmin_user = Usuario.objects.create_user(
                email=superadmin_email,
                password=superadmin_password,
                name=superadmin_name,
                lastname=superadmin_lastname,
                roles='superadmin',
                gimnasio=None,  # CLAVE: Sin gimnasio = acceso global
                must_change_password=False,
                is_active=True,
            )
            
            self.stdout.write(
                self.style.SUCCESS('[OK] Superadmin de plataforma creado: %s' % superadmin_email)
            )
            self.stdout.write('   Rol: superadmin (acceso global, sin gimnasio asignado)')
            self.stdout.write('   Nombre: %s %s' % (superadmin_name, superadmin_lastname))