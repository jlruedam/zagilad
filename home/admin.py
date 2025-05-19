from django.contrib import admin
from home import models
# Register your models here.



class AdmisionAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Información del Paciente', {
            'fields': ('documento_paciente', 'numero_estudio')
        }),
        ('Datos JSON', {
            'fields': ('json',),
            'classes': ('collapse',),  # Sección plegable
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = ('id', 'documento_paciente', 'numero_estudio', 'created_at', 'updated_at')

    # Filtros laterales
    list_filter = ('created_at', 'updated_at')

    # Campos de búsqueda
    search_fields = ('documento_paciente', 'numero_estudio')

    # Orden predeterminado
    ordering = ('-created_at',)

class AreaProgramaAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Información General', {
            'fields': ('identificador', 'nombre')
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = ('id', 'identificador', 'nombre', 'created_at', 'updated_at')
    
    # Filtros laterales
    list_filter = ('created_at', 'updated_at')

    # Campos de búsqueda
    search_fields = ('identificador', 'nombre')

    # Orden predeterminado
    ordering = ('-created_at',)

class RegionalAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Información General', {
            'fields': ('regional',)
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = ('id', 'regional', 'created_at', 'updated_at')

    # Filtros laterales
    list_filter = ('created_at', 'updated_at')

    # Campos de búsqueda
    search_fields = ('regional',)

    # Orden predeterminado
    ordering = ('-created_at',)

class ContratoMarcoAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Información del Contrato', {
            'fields': ('numero', 'contrato_subsidiado', 'contrato_contributivo')
        }),
        ('Detalles Adicionales', {
            'fields': ('observacion',),
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = ('id', 'numero', 'contrato_subsidiado', 'contrato_contributivo', 'created_at', 'updated_at')

    # Filtros laterales
    list_filter = ('created_at', 'updated_at')

    # Campos de búsqueda
    search_fields = ('numero', 'observacion')

    # Orden predeterminado
    ordering = ('-created_at',)

class ParametrosAreaProgramaAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Relaciones Principales', {
            'fields': ('area_programa', 'regional', 'unidad_funcional', 'punto_atencion', 'centro_costo', 'sede')
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = (
        'id', 'area_programa', 'regional', 'unidad_funcional', 
        'punto_atencion', 'centro_costo', 'sede', 'created_at', 'updated_at'
    )

    # Filtros laterales
    list_filter = ('area_programa', 'regional', 'sede', 'created_at', 'updated_at')

    # Campos de búsqueda
    search_fields = ('area_programa__nombre', 'regional__regional', 'unidad_funcional__nombre', 'centro_costo__nombre')

    # Orden predeterminado
    ordering = ('-created_at',)

class TipoActividadAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Información General', {
            'fields': ('grupo', 'nombre', 'cups', 'responsable', 'diagnostico')
        }),
        ('Detalles Adicionales', {
            'fields': ('finalidad','fuente', 'observacion', 'entrega'),
            'classes': ('collapse',),  # Sección plegable
        }),
        ('Relaciones', {
            'fields': ('contrato', 'tipo_servicio', 'area'),
            'classes': ('collapse',),  # Sección plegable
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = ('id', 'nombre', 'cups', 'grupo', 'contrato', 'tipo_servicio', 'area', 'created_at')
    
    # Filtros laterales
    list_filter = ('grupo', 'tipo_servicio', 'area', 'created_at')

    # Campos de búsqueda
    search_fields = ('nombre', 'cups', 'responsable', 'diagnostico', 'finalidad', 'fuente', 'observacion')

    # Orden predeterminado
    ordering = ('-created_at',)

class ActividadAdmin(admin.ModelAdmin):
    # Agrupación de campos con fieldsets
    fieldsets = (
        ('Información General', {
            'fields': (
                'tipo_fuente', 'identificador', 'fecha_servicio',
                'nombre_actividad', 'tipo_actividad', 'regional',
            )
        }),
        ('Datos del Paciente', {
            'fields': (
                'tipo_documento', 'documento_paciente', 'nombre_paciente',
                'diagnostico_p', 'diagnostico_1', 'diagnostico_2', 'diagnostico_3',
            )
        }),
        ('Relaciones y Estado', {
            'fields': (
                'finalidad','admision', 'parametros_programa', 'carga', 
                'inconsistencias', 'admisionada_otra_carga', 'datos_json',
            )
        }),
        ('Información del Médico', {
            'fields': ('documento_medico', 'medico'),
        }),
        ('Tiempos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),  # Sección plegable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at')

    # Listado
    list_display = (
        'id', 'tipo_fuente', 'fecha_servicio', 'nombre_actividad', 
        'documento_paciente', 'nombre_paciente', 'carga', 'finalidad',
        'admision', 'created_at', 'updated_at',
    )

    # Filtros laterales
    list_filter = (
        'tipo_fuente', 'fecha_servicio', 'tipo_actividad', 
        'regional', 'carga', 'admisionada_otra_carga', 'created_at'
    )

    # Campos de búsqueda
    search_fields = (
        'tipo_fuente', 'identificador', 'nombre_actividad', 
        'documento_paciente', 'nombre_paciente', 'regional',
    )

    # Orden predeterminado
    ordering = ('-created_at',)

class CargaAdmin(admin.ModelAdmin):
    # Agrupar campos con fieldsets
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'estado', 'observacion')
        }),
        ('Estadísticas de Actividades', {
            'fields': (
                'cantidad_actividades',
                'cantidad_actividades_ok',
                'cantidad_actividades_inconsistencias',
                'cantidad_actividades_admisionadas',
            ),
            'classes': ('collapse',),  # Hace que esta sección sea colapsable
        }),
        ('Detalles de Tiempo', {
            'fields': ('tiempo_procesamiento', 'created_at', 'updated_at'),
            'classes': ('collapse',),  # También colapsable
        }),
    )

    # Campos de solo lectura
    readonly_fields = ('created_at', 'updated_at', 'cantidad_actividades', 'cantidad_actividades_ok', 
                        'cantidad_actividades_inconsistencias', 'cantidad_actividades_admisionadas')

    # Opciones adicionales (opcional)
    list_display = ('id', 'usuario', 'estado', 'cantidad_actividades', 'created_at')
    search_fields = ('observacion', 'usuario__username')
    list_filter = ('estado', 'created_at')
    # Campos que se mostrarán en el listado del modelo
    list_display = (
        'id',
        'usuario',
        'estado',
        'cantidad_actividades',
        'cantidad_actividades_ok',
        'cantidad_actividades_inconsistencias',
        'cantidad_actividades_admisionadas',
        'observacion',
        'created_at',
        'updated_at',
    )

    # Campos para búsqueda
    search_fields = ('observacion', 'usuario__username')

    # Filtros laterales
    list_filter = ('estado', 'created_at', 'updated_at')

    # Campos de solo lectura (no editables desde el admin)
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'cantidad_actividades',
        'cantidad_actividades_ok',
        'cantidad_actividades_inconsistencias',
        'cantidad_actividades_admisionadas',
    )

    # Orden predeterminado del listado
    ordering = ('-created_at',)  # Orden descendente por fecha de creación

class TokenApiZeusAdmin(admin.ModelAdmin):
    list_display = ('id', 'token', 'vigente', 'vigencia', 'updated_at')
    list_filter = ('vigente', 'updated_at')
    search_fields = ('token',)
    readonly_fields = ('created_at', 'updated_at')

admin.site.register(models.Admision, AdmisionAdmin)
admin.site.register(models.AreaPrograma, AreaProgramaAdmin)
admin.site.register(models.Regional, RegionalAdmin)
admin.site.register(models.ContratoMarco, ContratoMarcoAdmin)
admin.site.register(models.ParametrosAreaPrograma, ParametrosAreaProgramaAdmin)
admin.site.register(models.TipoActividad, TipoActividadAdmin)
admin.site.register(models.Actividad, ActividadAdmin)
admin.site.register(models.Carga, CargaAdmin)
admin.site.register(models.TokenApiZeus, TokenApiZeusAdmin)

