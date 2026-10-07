"""Single audit entry point for membership operations (BR-1)."""

from django.db import transaction
from ..models import OperationLog


def log_operation(request, asignacion, operation_type, reason, details=None):
    """Create an OperationLog entry.

    Single entry point for all audit writes (BR-1).

    Args:
        request: Django request (for user, but gimnasio from assignment)
        asignacion: MembresiaAsignada - the assignment being operated on
        operation_type: str - one of OperationLog.OperationType values
        reason: str - verbatim reason (BR-2)
        details: dict - snapshot per operation_type (REQ-4)

    Returns:
        OperationLog: the created log entry
    """
    user = getattr(request, 'user', None)

    # gimnasio from assignment (REQ-2), never from request tenant context
    gimnasio = asignacion.miembro.gimnasio

    # usuario from authenticated user only
    usuario = user if getattr(user, 'is_authenticated', False) else None

    with transaction.atomic():
        return OperationLog.objects.create(
            gimnasio=gimnasio,
            membresia_asignada=asignacion,
            operation_type=operation_type,
            usuario=usuario,
            reason=reason,
            details=details or {},
        )