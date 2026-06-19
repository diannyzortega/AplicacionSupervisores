# comercial/admin.py
from django.contrib import admin
from .models import UserProfile, Region, Rol, Sucursal, Asesor, Categoria, AsesorCategoria, PlanificacionSemanal, ResultadosTarde, SeguimientoDiario, RegistroDiario



@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'user', 'id_rol', 'id_region', 'id_sucursal')
    search_fields = ('nombre', 'user__username')

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id_region', 'nombre_region')
    search_fields = ('nombre_region',)

@admin.register(Rol)
class RolAdmin(admin.ModelAdmin):
    list_display = ('id_rol', 'nombre_rol')
    search_fields = ('nombre_rol',)

@admin.register(Sucursal)
class SucursalAdmin(admin.ModelAdmin):
    list_display = ('id_sucursal', 'nombre_sucursal', 'id_region')
    search_fields = ('nombre_sucursal',)

@admin.register(Asesor)
class AsesorAdmin(admin.ModelAdmin):
    list_display = ('id_asesor', 'nombre_asesor', 'id_usuario', 'maestra', 'maestra_rebanadoras')
    search_fields = ('nombre_asesor',)

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id_categoria', 'nombre_categoria', 'mes', 'tipo_medida', 'obj_activacion', 'tipo_obj_activacion', 'obj_volumen', 'obj_profundidad')
    search_fields = ('nombre_categoria',)

@admin.register(AsesorCategoria)
class AsesorCategoriaAdmin(admin.ModelAdmin):
    list_display = ('id_asesor', 'id_categoria', 'obj_volumen')

@admin.register(SeguimientoDiario)
class SeguimientoDiarioAdmin(admin.ModelAdmin):
    list_display = ('id_asesor', 'id_categoria', 'act_lleva', 'vol_lleva', 'prof_lleva')

@admin.register(PlanificacionSemanal)
class PlanificacionSemanalAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'supervisor', 'region', 'sucursal', 'modalidad', 'asesor', 'zona')
    list_filter = ('fecha', 'region', 'sucursal', 'supervisor')
    search_fields = ('supervisor', 'asesor', 'zona')

@admin.register(ResultadosTarde)
class ResultadosTardeAdmin(admin.ModelAdmin):
    list_display = ('fecha_cierre', 'supervisor', 'region', 'sucursal', 'cajas_reales', 'monto_cobrado_real')
    list_filter = ('fecha_cierre', 'region', 'sucursal', 'supervisor')
    search_fields = ('supervisor',)

@admin.register(RegistroDiario)
class RegistroDiarioAdmin(admin.ModelAdmin):
    list_display = ('fecha', 'id_asesor', 'id_categoria', 'act_dia', 'vol_dia', 'prof_dia')
    list_filter = ('fecha', 'id_asesor', 'id_categoria')
