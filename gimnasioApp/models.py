from django.db import models
from datetime import timedelta, date
from decimal import Decimal
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser
from django.core.exceptions import ValidationError
from django.db.models import Sum


# ============================================================
# MODELO GIMNASIO - Para multi-tenant
# ============================================================
class Gimnasio(models.Model):
    """Representa cada gimnasio/cliente en el sistema multi-tenant."""
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200, blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'gimnasio'
        verbose_name = 'Gimnasio'
        verbose_name_plural = 'Gimnasios'
        ordering = ['name']
    
    def __str__(self):
        return self.name


# ============================================================
# MANAGER Y MODELO USUARIO
# ============================================================
class UserManager(BaseUserManager):
    def create_user(self, email, password, **extra_fields):
        """
        Crea un usuario.
        """
        if not email:
            raise ValueError('Los usuarios deben tener un correo electrónico')
        
        user = self.model(email=self.normalize_email(email), **extra_fields)
        user.set_password(password)
        user.save()
        return user

class Usuario(AbstractBaseUser):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=45)
    lastname = models.CharField(max_length=50)
    #user = models.CharField(max_length=30, unique=True)
    avatar = models.ImageField(upload_to='fotos/', null=True, blank=True, default='')
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='usuarios',
        null=False,
        blank=False
    )
        
    OPCIONES_ROL = [
        ('recepcion', 'Recepcionista'),
        ('admin', 'Administrador')
    ]
    roles = models.CharField(max_length=10, choices=OPCIONES_ROL, default='recepcion')
    #password = models.CharField(max_length=300)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    #Usamos el UserManager personalizado
    objects = UserManager()

    #Se define el campo de autenticación sea el email
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name', 'lastname']

    def full_name(self):
        return '{} {}'.format(self.name, self.lastname)

    def __str__(self):
        return self.full_name()
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        db_table = 'usuario'
        ordering = ['created_at']

class UsuarioGym(models.Model):
    name = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    address = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='miembros',
        null=False,
        blank=False
    )

    def __str__(self):
        return f"{self.name} {self.lastname}"
    
    class Meta:
        verbose_name = 'UsuarioGym'
        verbose_name_plural = 'UsuarioGyms'
        db_table = 'usuarioGym'
        ordering = ['-created_at']
    
class UsuarioGymDay(models.Model):
    name = models.CharField(max_length=100)
    lastname = models.CharField(max_length=100)
    phone = models.CharField(max_length=10)
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    dateInitial = models.DateField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='miembros_diarios',
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'UsuarioGymDay'
        verbose_name_plural = 'UsuarioGymDays'
        db_table = 'usuarioGymDay'
        ordering = ['-created_at']

class Membresia(models.Model):
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveIntegerField(help_text="Duración en días (1-365)")
    max_multiplier = models.PositiveIntegerField(default=1, help_text="Máximo multiplicador permitido (1 = no multiplicable)")
    is_active = models.BooleanField(default=True)
    
    # FK a Gimnasio para multi-tenant
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='membresias',
        null=False,
        blank=False
    )

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = 'Membresia'
        verbose_name_plural = 'Membresias'
        db_table = 'membresia'
        unique_together = ('gimnasio', 'name')

class MembresiaAsignada(models.Model):
    gimnasio = models.ForeignKey(Gimnasio, on_delete=models.CASCADE, related_name='membresias_asignadas', null=False, blank=False)
    miembro = models.ForeignKey(UsuarioGym, on_delete=models.CASCADE, related_name='miembro')
    membresia = models.ForeignKey(Membresia, on_delete=models.CASCADE)
    multiplier = models.DecimalField(default=1, max_digits=4, decimal_places=1, help_text="Multiplicador de duración/precio (1 = sin multiplicar)")
    discount_percent = models.DecimalField(default=0, max_digits=5, decimal_places=2, help_text="Descuento porcentual (0-100)")
    dateInitial = models.DateField()
    dateFinal = models.DateField(editable=False, null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    notified_at = models.DateTimeField(null=True, blank=True, help_text="Fecha en que se marcó como notificada/leída")

    class Meta:
        verbose_name = 'MembresiaAsignada'
        verbose_name_plural = 'MembresiaAsignadas'
        db_table = 'membresiaAsignada'
        ordering = ['-dateInitial']
    
    def save(self, *args, **kwargs):
        if not self.gimnasio_id and self.miembro_id:
            self.gimnasio = self.miembro.gimnasio
        # Ensure dateInitial is a date object, not a string
        inicio = self.dateInitial
        if isinstance(inicio, str):
            try:
                partes = inicio.split('-')
                inicio = date(int(partes[0]), int(partes[1]), int(partes[2]))
            except (IndexError, ValueError):
                raise ValidationError("Formato de fecha inválido. Use YYYY-MM-DD.")
        if not self.pk:  # Only on creation
            if int(self.multiplier) > self.membresia.max_multiplier:
                if self.membresia.max_multiplier <= 1:
                    raise ValidationError("Esa membresía no se puede multiplicar")
                raise ValidationError(
                    f"Esa membresía solo permite hasta {self.membresia.max_multiplier} periodos"
                )
            mult = Decimal(str(self.multiplier))
            disc = Decimal(str(self.discount_percent or 0))
            dias_totales = int(self.membresia.duration * mult)
            self.dateFinal = inicio + timedelta(days=dias_totales)
            self.price = self.membresia.price * mult * (Decimal('1') - disc / Decimal('100'))
        else:
            mult = Decimal(str(self.multiplier or 1))
            disc = Decimal(str(self.discount_percent or 0))
            dias_totales = int(self.membresia.duration * mult)
            self.dateFinal = inicio + timedelta(days=dias_totales)
            self.price = self.membresia.price * mult * (Decimal('1') - disc / Decimal('100'))
        super().save(*args, **kwargs)

    def clean(self):
        if MembresiaAsignada.objects.filter(miembro=self.miembro,
                                            dateInitial__lte=self.dateFinal,
                                            dateFinal__gte=self.dateInitial).exclude(pk=self.pk).exists():
            raise ValidationError('Ya existe una membresia asignada para este usuario en el rango de fechas indicado')
   
    @property
    def activa(self):
        hoy = date.today()
        return self.dateInitial <= hoy <= self.dateFinal

    @property
    def total_pagado(self):
        return self.pagos.aggregate(total=Sum('monto'))['total'] or Decimal('0')

    @property
    def saldo_pendiente(self):
        return self.price - self.total_pagado

    @property
    def estado_pago(self):
        if self.total_pagado >= self.price:
            return 'paid'
        elif self.total_pagado > 0:
            return 'partial'
        return 'pending'

    def __str__(self):
        return f"{self.miembro.name} - {self.miembro.lastname} - {self.membresia.name}"


class PagoMembresia(models.Model):
    METODO_PAGO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('transferencia', 'Transferencia'),
        ('nequi', 'Nequi'),
    ]

    membresia_asignada = models.ForeignKey(
        MembresiaAsignada,
        on_delete=models.CASCADE,
        related_name='pagos'
    )
    monto = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_pago = models.DateTimeField(auto_now_add=True)
    metodo_pago = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES)
    nota = models.TextField(blank=True, default='')

    class Meta:
        verbose_name = 'Pago Membresia'
        verbose_name_plural = 'Pagos Membresia'
        db_table = 'pago_membresia'
        ordering = ['-fecha_pago']

    def __str__(self):
        return f"Pago {self.monto} - {self.metodo_pago} ({self.fecha_pago.strftime('%d/%m/%Y') if self.fecha_pago else '--'})"    


# ============================================================
# CALENDARIO — TIPO DE EVENTO Y EVENTO DE CALENDARIO
# ============================================================

class TipoEvento(models.Model):
    """Tipo de evento del calendario (multi-tenant por gimnasio)."""
    nombre = models.CharField(max_length=100)
    color = models.CharField(max_length=7)  # e.g. #FF0000
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='tipos_evento',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = 'TipoEvento'
        verbose_name_plural = 'TipoEventos'
        db_table = 'tipo_evento'
        ordering = ['nombre']


class EventoCalendario(models.Model):
    """Evento del calendario (multi-tenant por gimnasio)."""
    titulo = models.CharField(max_length=200)
    fecha_inicio = models.DateTimeField()
    fecha_fin = models.DateTimeField()
    descripcion = models.TextField(blank=True, default='')
    tipo = models.ForeignKey(
        TipoEvento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos'
    )
    relacion_tipo = models.CharField(max_length=50, null=True, blank=True, default='')
    relacion_id = models.IntegerField(null=True, blank=True)
    created_by = models.ForeignKey(
        Usuario,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='eventos_creados'
    )
    gimnasio = models.ForeignKey(
        Gimnasio,
        on_delete=models.CASCADE,
        related_name='eventos_calendario',
        null=False,
        blank=False
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titulo

    class Meta:
        verbose_name = 'EventoCalendario'
        verbose_name_plural = 'EventoCalendarios'
        db_table = 'evento_calendario'
        ordering = ['fecha_inicio']