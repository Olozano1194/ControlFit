from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError


def _catch_model_error(e: DjangoValidationError):
    from django.core.exceptions import ValidationError as DJE
    if isinstance(e, DJE):
        if hasattr(e, 'error_dict'):
            raise serializers.ValidationError(e.message_dict)
        msg = e.messages[0] if e.messages else str(e)
        raise serializers.ValidationError(msg)
    raise e

