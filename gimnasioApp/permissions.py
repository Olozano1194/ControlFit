from rest_framework.permissions import BasePermission


class IsAdminUser(BasePermission):
    """
    Permiso personalizado: Solo usuarios con rol 'admin' o 'superadmin' pueden acceder.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.roles in ['admin', 'superadmin']
        )


class IsRecepcionUser(BasePermission):
    """
    Permiso personalizado: Usuarios con rol 'recepcion', 'admin' O 'superadmin' pueden acceder.
    Los recepcionistas pueden leer y escribir, pero no eliminar.
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        return request.user.roles in ['admin', 'recepcion', 'superadmin']
    
    def has_object_permission(self, request, view, obj):
        # superadmin y admin pueden todo
        if request.user.roles in ['admin', 'superadmin']:
            return True
        # recepcionistas no pueden eliminar
        if request.method == 'DELETE' and request.user.roles == 'recepcion':
            return False
        return True


class IsOwnerOrAdmin(BasePermission):
    """
    Permiso: El usuario puede acceder solo a sus propios objetos,
    o los admins pueden acceder a todos.
    """
    def has_object_permission(self, request, view, obj):
        if request.user.roles == 'admin':
            return True
        
        # Verificar si el objeto tiene usuario
        if hasattr(obj, 'user'):
            return obj.user == request.user
        if hasattr(obj, 'usuario'):
            return obj.usuario == request.user
        
        return False


class IsSuperAdmin(BasePermission):
    """
    Permiso personalizado: Solo usuarios con rol 'superadmin' pueden acceder.
    """
    def has_permission(self, request, view):
        return (
            request.user 
            and request.user.is_authenticated 
            and request.user.roles == 'superadmin'
        )