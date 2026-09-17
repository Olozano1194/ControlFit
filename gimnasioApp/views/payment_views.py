from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from ..serializers.payment_serializer import PagoMembresiaSerializer
from ..models.membership_model import MembresiaAsignada
from ..models.payment_model import PagoMembresia
from ..permissions import IsRecepcionUser, RequirePasswordChange


class PagoMembresiaViewSet(viewsets.ModelViewSet):
    serializer_class = PagoMembresiaSerializer
    permission_classes = [IsAuthenticated, IsRecepcionUser, RequirePasswordChange]

    def get_membresia_asignada(self):
        pk = self.kwargs.get('pk')
        return get_object_or_404(
            MembresiaAsignada.objects.filter(miembro__gimnasio=self.request.gimnasio),
            pk=pk
        )

    def get_queryset(self):
        membresia = self.get_membresia_asignada()
        return PagoMembresia.objects.filter(
            membresia_asignada=membresia
        ).order_by('-fecha_pago')

    def perform_create(self, serializer):
        membresia = self.get_membresia_asignada()
        serializer.save(membresia_asignada=membresia)

    def get_serializer_context(self):
        context = super().get_serializer_context()
        try:
            membresia = self.get_membresia_asignada()
            context['membresia_asignada'] = membresia
        except Exception:
            pass
        return context