from rest_framework import serializers
from django.db import transaction
from django.core.exceptions import ValidationError as DjangoValidationError
from .models import Gimnasio, Usuario, UsuarioGym, UsuarioGymDay, Membresia, MembresiaAsignada, PagoMembresia, TipoEvento, EventoCalendario, Notification
from datetime import timedelta, date
from decimal import Decimal

#token
from rest_framework.authtoken.models import Token


# ============================================================
# GIMNASIO SERIALIZER
# ============================================================

class GimnasioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Gimnasio
        fields = '__all__'
        read_only_fields = ('id', 'created_at')


# ============================================================
# USUARIO SERIALIZER
# ============================================================

class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    avatar = serializers.ImageField(required=False, allow_null=True)
    gimnasio_name = serializers.CharField(source='gimnasio.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'name', 'lastname', 'roles', 'gimnasio', 'gimnasio_name',
                  'avatar', 'is_active', 'created_at', 'password']
        read_only_fields = ('id', 'created_at', 'is_active', 'gimnasio', 'gimnasio_name')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if self.instance:
            self.fields['email'].required = False
    
    def validate_password(self, value):
        if value and len(value) < 6:
            raise serializers.ValidationError("La contraseña debe tener al menos 6 caracteres")
        return value
    
    def create(self, validated_data):
        """
        Crea usuario. Usa request.gimnasio si está disponible, si no (registro), crea gimnasio automáticamente.
        """
        password = validated_data.pop('password')
        # Remover gimnasio de validated_data si viene de perform_create
        validated_data.pop('gimnasio', None)

        request = self.context.get('request')
        gimnasio = getattr(request, 'gimnasio', None)

        if gimnasio is None:
            # Flujo de registro: crear gimnasio automáticamente
            email = validated_data.get('email', '')
            email_prefix = email.split('@')[0].replace('.', ' ').title() if '@' in email else email
            gimnasio = Gimnasio.objects.create(
                name=f"Gimnasio {email_prefix}"
            )

        user = Usuario(gimnasio=gimnasio, **validated_data)
        user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        # Handle password separately
        if 'password' in validated_data:
            password = validated_data.pop('password')
            instance.set_password(password)
        
        # Delete old avatar if new one is provided
        avatar = validated_data.get('avatar', None)
        if avatar and instance.avatar and instance.avatar.name:
            instance.avatar.delete(save=False)
        
        # Continue with normal update using super()
        instance = super().update(instance, validated_data)
        return instance


# ============================================================
# MIEMBROS DEL GIMNASIO
# ============================================================

class UsuarioGymSerializer(serializers.ModelSerializer):
    gimnasio_name = serializers.CharField(source='gimnasio.name', read_only=True, allow_null=True)
    initial_membership_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    dateInitial = serializers.DateField(write_only=True, required=False, allow_null=True)
    multiplier = serializers.DecimalField(max_digits=4, decimal_places=1, default=Decimal('1'), write_only=True, required=False)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'), write_only=True, required=False)

    class Meta:
        model = UsuarioGym
        fields = ['id', 'name', 'lastname', 'phone', 'address', 'gimnasio',
                  'gimnasio_name', 'created_at', 'initial_membership_id', 'dateInitial',
                  'multiplier', 'discount_percent']
        read_only_fields = ('id', 'created_at', 'gimnasio')

    def create(self, validated_data):
        initial_membership_id = validated_data.pop('initial_membership_id', None)
        date_initial = validated_data.pop('dateInitial', None)
        multiplier = validated_data.pop('multiplier', Decimal('1'))
        discount_percent = validated_data.pop('discount_percent', Decimal('0'))

        # Remover cualquier gimnasio de los datos validados (usar el del middleware)
        validated_data.pop('gimnasio', None)

        # Obtener gimnasio del request (seteado por el middleware)
        request = self.context.get('request')
        gimnasio = getattr(request, 'gimnasio', None)

        if gimnasio is None:
            raise serializers.ValidationError("No se pudo determinar el gimnasio del request")

        validated_data['gimnasio'] = gimnasio

        with transaction.atomic():
            miembro = UsuarioGym.objects.create(**validated_data)

            if initial_membership_id:
                try:
                    membresia = Membresia.objects.get(
                        id=initial_membership_id,
                        gimnasio=gimnasio
                    )
                except Membresia.DoesNotExist:
                    raise serializers.ValidationError({"initial_membership_id": "Membresía no encontrada en tu gimnasio"})
                try:
                    MembresiaAsignada.objects.create(
                        miembro=miembro,
                        membresia=membresia,
                        dateInitial=date_initial or date.today(),
                        multiplier=multiplier,
                        discount_percent=discount_percent
                    )
                except DjangoValidationError as e:
                    _catch_model_error(e)

            return miembro

    def update(self, instance, validated_data):
        initial_membership_id = validated_data.pop('initial_membership_id', None)
        date_initial = validated_data.pop('dateInitial', None)
        multiplier = validated_data.pop('multiplier', Decimal('1'))
        discount_percent = validated_data.pop('discount_percent', Decimal('0'))
        instance = super().update(instance, validated_data)
        if initial_membership_id:
            try:
                membresia = Membresia.objects.get(id=initial_membership_id, gimnasio=instance.gimnasio)
            except Membresia.DoesNotExist:
                raise serializers.ValidationError({'initial_membership_id': 'Membresia no encontrada en tu gimnasio'})
            try:
                MembresiaAsignada.objects.create(
                    miembro=instance, membresia=membresia,
                    dateInitial=date_initial or date.today(),
                    multiplier=multiplier, discount_percent=discount_percent
                )
            except DjangoValidationError as e:
                _catch_model_error(e)
        return instance


class UsuarioGymDaySerializer(serializers.ModelSerializer):
    gimnasio_name = serializers.CharField(source='gimnasio.name', read_only=True, allow_null=True)
    dateInitial = serializers.DateField(format="%d-%m-%Y", input_formats=['%Y-%m-%d', '%d-%m-%Y'])
    
    class Meta:
        model = UsuarioGymDay
        fields = ['id', 'name', 'lastname', 'phone', 'dateInitial', 'price',
                  'gimnasio', 'gimnasio_name', 'created_at']
        read_only_fields = ('id', 'created_at', 'gimnasio')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.dateInitial:
            representation['dateInitial'] = instance.dateInitial.strftime("%d-%m-%Y")        
        return representation

    def create(self, validated_data):
        # Remover cualquier gimnasio de los datos validados
        validated_data.pop('gimnasio', None)
        
        # Obtener gimnasio del request
        request = self.context.get('request')
        gimnasio = getattr(request, 'gimnasio', None)
        
        if gimnasio is None:
            raise serializers.ValidationError("No se pudo determinar el gimnasio del request")
        
        validated_data['gimnasio'] = gimnasio
        return super().create(validated_data)


# ============================================================
# MEMBRESIAS
# ============================================================

class MembresiasSerializer(serializers.ModelSerializer):
    gimnasio_name = serializers.CharField(source='gimnasio.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Membresia
        fields = ['id', 'name', 'price', 'duration', 'max_multiplier', 'is_active', 'gimnasio', 'gimnasio_name']
        read_only_fields = ('id', 'gimnasio',)

    def validate_duration(self, value):
        if value < 1 or value > 365:
            raise serializers.ValidationError("La duración debe estar entre 1 y 365 días")
        return value

    def create(self, validated_data):
        # Remover cualquier gimnasio de los datos validados
        validated_data.pop('gimnasio', None)
        
        # Obtener gimnasio del request
        request = self.context.get('request')
        gimnasio = getattr(request, 'gimnasio', None)
        
        if gimnasio is None:
            raise serializers.ValidationError("No se pudo determinar el gimnasio del request")
        
        validated_data['gimnasio'] = gimnasio
        return super().create(validated_data)


class MembresiaAsignadaSerializer(serializers.ModelSerializer):
    miembro_details = UsuarioGymSerializer(source='miembro', read_only=True)
    membresia_details = MembresiasSerializer(source='membresia', read_only=True)

    dateInitial = serializers.DateField(format="%d-%m-%Y", input_formats=['%Y-%m-%d', '%d-%m-%Y'])
    dateFinal = serializers.DateField(format="%d-%m-%Y", input_formats=['%Y-%m-%d', '%d-%m-%Y'], read_only=True)

    multiplier = serializers.DecimalField(max_digits=4, decimal_places=1, default=Decimal('1'))
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    total_pagado = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    saldo_pendiente = serializers.DecimalField(max_digits=10, decimal_places=2, read_only=True)
    estado_pago = serializers.CharField(read_only=True)

    class Meta:
        model = MembresiaAsignada
        fields = ['id', 'miembro', 'membresia', 'miembro_details', 'membresia_details',
                  'dateInitial', 'dateFinal', 'price', 'multiplier', 'discount_percent',
                  'total_pagado', 'saldo_pendiente', 'estado_pago']
        read_only_fields = ('id', 'price', 'dateFinal')

    def validate_multiplier(self, value):
        if value < 1:
            raise serializers.ValidationError("El multiplicador debe ser al menos 1")
        return value

    def validate(self, data):           
        miembro = data.get('miembro') or (self.instance.miembro if self.instance else None)
        inicio = data.get('dateInitial') or (self.instance.dateInitial if self.instance else None)
        membresia = data.get('membresia') or (self.instance.membresia if self.instance else None)
        
        if not miembro or not membresia:
            raise serializers.ValidationError("Miembro y membresía son requeridos")
        
        # Verificar que miembro y membresia sean del mismo gimnasio
        if miembro.gimnasio != membresia.gimnasio:
            raise serializers.ValidationError(
                "El miembro y la membresía deben pertenecer al mismo gimnasio"
            )
        
        # Verificar que ambos pertenezcan al gimnasio del request
        request = self.context.get('request')
        gimnasio = getattr(request, 'gimnasio', None)
        if gimnasio and miembro.gimnasio != gimnasio:
            raise serializers.ValidationError(
                "El miembro no pertenece a tu gimnasio"
            )
        
        # Validar multiplier contra max_multiplier de la membresía
        multiplier = data.get('multiplier', getattr(self.instance, 'multiplier', 1)) or 1
        if int(multiplier) > membresia.max_multiplier:
            if membresia.max_multiplier <= 1:
                raise serializers.ValidationError("Esa membresía no se puede multiplicar")
            raise serializers.ValidationError(
                f"Esa membresía solo permite hasta {membresia.max_multiplier} periodos"
            )
        
        # Verificar fechas considerando el multiplier
        dias_totales = int(membresia.duration * Decimal(str(multiplier)))
        expected_final = inicio + timedelta(days=dias_totales)
        
        suscripcion = MembresiaAsignada.objects.filter(
            miembro=miembro, 
            dateInitial__lte=expected_final, 
            dateFinal__gte=inicio
        ).exclude(pk=self.instance.pk if self.instance else None)
        
        if suscripcion.exists():
            raise serializers.ValidationError(
                'El miembro ya tiene una suscripción activa en este rango de fechas'
            )
        return data        

    def create(self, validated_data):
        # Price calculation is handled by model.save()
        try:
            return super().create(validated_data)
        except DjangoValidationError as e:
            _catch_model_error(e)
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if instance.dateInitial:
            representation['dateInitial'] = instance.dateInitial.strftime("%d-%m-%Y")
        if instance.dateFinal:
            representation['dateFinal'] = instance.dateFinal.strftime("%d-%m-%Y")
        return representation


# Helper: convierte ValidationError de Django a DRF
def _catch_model_error(e: DjangoValidationError):
    from django.core.exceptions import ValidationError as DJE
    if isinstance(e, DJE):
        if hasattr(e, 'error_dict'):
            raise serializers.ValidationError(e.message_dict)
        msg = e.messages[0] if e.messages else str(e)
        raise serializers.ValidationError(msg)
    raise e


# ============================================================
# PAGO MEMBRESIA SERIALIZER
# ============================================================

class PagoMembresiaSerializer(serializers.ModelSerializer):
    fecha_pago = serializers.DateTimeField(read_only=True, format="%Y-%m-%dT%H:%M:%S%z")

    class Meta:
        model = PagoMembresia
        fields = ['id', 'membresia_asignada', 'monto', 'fecha_pago', 'metodo_pago', 'nota']
        read_only_fields = ['id', 'fecha_pago', 'membresia_asignada']

    def validate_monto(self, value):
        if value <= 0:
            raise serializers.ValidationError("El monto debe ser mayor a cero")
        return value

    def validate(self, data):
        membresia = self.context.get('membresia_asignada') or data.get('membresia_asignada')
        if membresia:
            monto = data.get('monto')
            if monto and monto > membresia.saldo_pendiente:
                raise serializers.ValidationError({
                    'monto': f'El monto excede el saldo pendiente ({membresia.saldo_pendiente})'
                })
        return data


# ============================================================
# CALENDARIO — TIPO EVENTO Y EVENTO CALENDARIO
# ============================================================

class TipoEventoSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = ['id', 'nombre', 'color', 'gimnasio', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'created_at')


class TipoEventoSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = TipoEvento
        fields = ['id', 'nombre', 'color']


class EventoCalendarioSerializer(serializers.ModelSerializer):
    tipo_detalle = TipoEventoSimpleSerializer(source='tipo', read_only=True)
    descripcion = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')

    class Meta:
        model = EventoCalendario
        fields = ['id', 'titulo', 'fecha_inicio', 'fecha_fin', 'descripcion',
                  'tipo', 'tipo_detalle', 'relacion_tipo', 'relacion_id',
                  'created_by', 'gimnasio', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'created_by', 'created_at')

    def validate(self, data):
        inicio = data.get('fecha_inicio') or (self.instance.fecha_inicio if self.instance else None)
        fin = data.get('fecha_fin') or (self.instance.fecha_fin if self.instance else None)
        if inicio and fin and fin <= inicio:
            raise serializers.ValidationError("fecha_fin must be after fecha_inicio")
        # Normalize explicit null to '' only when the field is actually present.
        # On partial updates (PATCH) omitting descripcion, DRF skips the field,
        # so it must NOT be re-injected here or the stored value is erased.
        if 'descripcion' in data and data.get('descripcion') is None:
            data['descripcion'] = ''
        return data


# ============================================================
# NOTIFICACIONES
# ============================================================

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'tipo', 'titulo', 'mensaje', 'fecha', 'relacion_tipo',
                  'relacion_id', 'link', 'whatsapp_link', 'is_read', 'read_at', 'created_at']
        read_only_fields = ('id', 'gimnasio', 'is_read', 'read_at', 'created_at')