from django.contrib import admin
from django.urls import path
from home import views


urlpatterns = [
   
    
    # Actividades
    path('vistaCargaActividades/', views.vista_carga_actividades),
    path('vistaGrabarAdmisiones/', views.vista_grabar_admisiones),
    path('cargaActividades/', views.cargar_actividades),
    path('cargarTiposActividad/', views.cargar_tipos_actividad),
    path('vistaActividadesAdmisionadas/', views.vista_actividades_admisionadas),
    path('vistaActividadesInconsistencias/', views.vista_actividades_inconsistencias),
    path('tiposActividad/', views.tipos_actividad),
    path('parametrosAreaPrograma/', views.parametros_area_programa),
    path('listarActividadesInconsistencias/', views.listar_actividades_inconsistencias),
    path('listarActividadesAdmisionadas/', views.listar_actividades_admisionadas),
    path('listarActividadesCarga/<num_carga>', views.listar_actividades_carga),
    # Grabar admisiones
    path('grabarAdmisionPrueba/', views.grabar_admision_prueba),
    path('consultarAdmisionesPrueba/', views.consultar_admisiones_prueba),
    # path('grabarAdmisiones/', views.grabar_admisiones),
    path('admisionarActividadesCarga/<id_carga>', views.admisionar_actividades_carga),
    path('admisionarActividadIndividual/<id_actividad>/<pagina>', views.admisionar_actividad_individual),
    path('eliminarActividadesInconsistenciaCarga/<id_carga>/<tipo_inconsistencia>', views.eliminar_actividades_inconsistencia_carga),
    path('eliminarActividadIndividual/<id_actividad>/<pagina>', views.eliminar_actividad_individual),
    # Carga de Archivos
    path('cargarActividades/', views.cargar_actividades),
    path('procesarCargueActividades/', views.procesarCargue),
    path('informeCargas/', views.informe_cargas),
    path('verCarga/<id_carga>/<pagina>', views.ver_carga),
    path('descargarArchivo/<nombre_archivo>', views.descargar_archivo),
    path('exportarCargaExcel/<id_carga>/<tipo>', views.exportar_carga_excel),
    # Administración
    path('administrador/', views.vista_administrador),
    path('cargarConfiguracionArranque/', views.cargar_configuracion_arranque),
]

