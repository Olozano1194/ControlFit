from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from .helper_error import _catch_model_error
from ..models import Membresia, MembresiaAsignada
from .member_serializer import UsuarioGymSerializer
from datetime import timedelta
from decimal import Decimal


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