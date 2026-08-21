from django.contrib import admin
from .models import Gimnasio, Usuario, UsuarioGym, UsuarioGymDay, Membresia, MembresiaAsignada


@admin.register(Gimnasio)
class GimnasioAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'address')
    ordering = ('name',)


@admin.register(Usuario)
class UsuarioAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'lastname', 'roles', 'gimnasio', 'is_active', 'created_at')
    list_filter = ('roles', 'is_active', 'gimnasio')
    search_fields = ('email', 'name', 'lastname')
    ordering = ('-created_at',)


@admin.register(UsuarioGym)
class UsuarioGymAdmin(admin.ModelAdmin):
    list_display = ('name', 'lastname', 'phone', 'address', 'gimnasio', 'created_at')
    list_filter = ('gimnasio',)
    search_fields = ('name', 'lastname', 'phone')
    ordering = ('-created_at',)


@admin.register(UsuarioGymDay)
class UsuarioGymDayAdmin(admin.ModelAdmin):
    list_display = ('name', 'lastname', 'phone', 'dateInitial', 'price', 'gimnasio', 'created_at')
    list_filter = ('gimnasio',)
    search_fields = ('name', 'lastname', 'phone')
    ordering = ('-created_at',)


@admin.register(Membresia)
class MembresiaAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration', 'gimnasio', 'is_active')
    list_filter = ('name', 'is_active', 'gimnasio')
    search_fields = ('name',)


@admin.register(MembresiaAsignada)
class MembresiaAsignadaAdmin(admin.ModelAdmin):
    list_display = ('miembro', 'membresia', 'dateInitial', 'dateFinal', 'price', 'activa')
    list_filter = ('membresia',)
    search_fields = ('miembro__name', 'miembro__lastname')
    ordering = ('-dateInitial',)
    
    def activa(self, obj):
        return obj.activa
    activa.boolean = True

from .models import DemoRequest

@admin.register(DemoRequest)
class DemoRequestAdmin(admin.ModelAdmin):
    list_display = ('nombre_gimnasio', 'nombre', 'email', 'telefono', 'estado', 'fecha_solicitud')
    list_filter = ('estado', 'fecha_solicitud')
    search_fields = ('nombre_gimnasio', 'nombre', 'email', 'telefono')
    ordering = ('-fecha_solicitud',)
    list_editable = ('estado',)