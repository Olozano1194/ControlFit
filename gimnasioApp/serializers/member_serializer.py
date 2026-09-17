from rest_framework import serializers
from django.db import transaction
from ..models.member_model import UsuarioGym, UsuarioGymDay
from ..models.membership_model import Membresia, MembresiaAsignada
from django.core.exceptions import ValidationError as DjangoValidationError
from .helper_error import _catch_model_error
from datetime import date
from decimal import Decimal



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