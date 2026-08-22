from rest_framework import viewsets


class MultiTenantViewSetMixin:
    gimnasio_field = 'gimnasio'  # Override in ViewSet if different
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Superadmin ve todo sin filtro de gimnasio
        if hasattr(self.request, 'user') and self.request.user.is_authenticated:
            if getattr(self.request.user, 'roles', None) == 'superadmin':
                return queryset
        
        if self.request.gimnasio:
            if self.gimnasio_field == 'gimnasio':
                return queryset.filter(gimnasio=self.request.gimnasio)
            else:
                # Handle nested fields like 'miembro__gimnasio'
                return queryset.filter(**{self.gimnasio_field: self.request.gimnasio})
        return queryset.none()
    
    def perform_create(self, serializer):
        # Superadmin no asigna gimnasio automáticamente
        if hasattr(self.request, 'user') and getattr(self.request.user, 'roles', None) == 'superadmin':
            serializer.save()
        else:
            serializer.save(gimnasio=self.request.gimnasio)
    
    def perform_update(self, serializer):
        # Superadmin no cambia gimnasio automáticamente
        if hasattr(self.request, 'user') and getattr(self.request.user, 'roles', None) == 'superadmin':
            serializer.save()
        else:
            serializer.save(gimnasio=self.request.gimnasio)