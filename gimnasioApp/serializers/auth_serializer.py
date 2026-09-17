from rest_framework import serializers


# ============================================================
# PASSWORD CHANGE SERIALIZER
# ============================================================

class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change endpoint.
    
    Validates old_password, new_password, and confirm_password.
    """
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=8)
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Las contraseñas no coinciden.'})
        return attrs