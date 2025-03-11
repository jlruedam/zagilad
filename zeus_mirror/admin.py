
# Register your models here.
from django.contrib import admin
from .models import Contrato, UnidadFuncional, PuntoAtencion, CentroCosto, Sede, TipoServicio, Medico

@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'empresa', 'numero', 'regimen', 'activo', 'created_at')
    search_fields = ('codigo', 'empresa', 'numero')
    list_filter = ('activo', 'regimen')

@admin.register(UnidadFuncional)
class UnidadFuncionalAdmin(admin.ModelAdmin):
    list_display = ('id_zeus', 'codigo', 'descripcion', 'id_sede', 'created_at')
    search_fields = ('codigo', 'descripcion')
    list_filter = ('id_sede',)

@admin.register(PuntoAtencion)
class PuntoAtencionAdmin(admin.ModelAdmin):
    list_display = ('id_zeus', 'codigo', 'nombre', 'nit', 'departamento', 'municipio', 'created_at')
    search_fields = ('codigo', 'nombre', 'nit')
    list_filter = ('departamento', 'municipio')

@admin.register(CentroCosto)
class CentroCostoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nombre', 'tipo', 'stock', 'activo_zeus', 'created_at')
    search_fields = ('codigo', 'nombre')
    list_filter = ('tipo', 'stock')

@admin.register(Sede)
class SedeAdmin(admin.ModelAdmin):
    list_display = ('id_zeus', 'nit', 'razon_social', 'codigo_eps', 'ciudad', 'departamento', 'created_at')
    search_fields = ('nit', 'razon_social', 'codigo_eps')
    list_filter = ('ciudad', 'departamento')

@admin.register(TipoServicio)
class TipoServicioAdmin(admin.ModelAdmin):
    list_display = ('fuente', 'id_zeus', 'nombre', 'tipo', 'tipo_servicio', 'created_at')
    search_fields = ('nombre', 'tipo')
    list_filter = ('tipo_servicio',)

@admin.register(Medico)
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'documento', 'nombre', 'created_at')
    search_fields = ('codigo', 'documento', 'nombre')