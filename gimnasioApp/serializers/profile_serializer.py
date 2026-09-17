from rest_framework import serializers
from ..models.gym_model import Gimnasio
from ..models.user_model import Usuario


class UsuarioSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    avatar = serializers.ImageField(required=False, allow_null=True)
    gimnasio_name = serializers.CharField(source='gimnasio.name', read_only=True, allow_null=True)
    
    class Meta:
        model = Usuario
        fields = ['id', 'email', 'name', 'lastname', 'roles', 'gimnasio', 'gimnasio_name',
                  'avatar', 'is_active', 'created_at', 'password', 'must_change_password']
        read_only_fields = ('id', 'created_at', 'is_active', 'gimnasio', 'gimnasio_name', 'must_change_password')

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
        Para superadmin, no requiere gimnasio.
        """
        password = validated_data.pop('password')
        # Remover gimnasio de validated_data si viene de perform_create
        validated_data.pop('gimnasio', None)

        request = self.context.get('request')
        gimnasio = getattr(request, 'gimnasio', None)
        roles = validated_data.get('roles', 'recepcion')

        # Superadmin no requiere gimnasio
        if roles == 'superadmin':
            gimnasio = None
        elif gimnasio is None:
            # Flujo de registro normal: crear gimnasio automáticamente
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