from django.contrib import admin
from django.urls import path
from home import views


urlpatterns = [
    # Actividades
    path('vistaCargaActividades/', views.vista_carga_actividades, name='vista_carga_actividades'),
    path('vistaGrabarAdmisiones/', views.vista_grabar_admisiones, name='vista_grabar_admisiones'),
    path('cargaActividades/', views.cargar_actividades, name='carga_actividades'),
    path('cargarTiposActividad/', views.cargar_tipos_actividad, name='cargar_tipos_actividad'),
    path('vistaActividadesAdmisionadas/', views.vista_actividades_admisionadas, name='vista_actividades_admisionadas'),
    path('vistaActividadesInconsistencias/', views.vista_actividades_inconsistencias, name='vista_actividades_inconsistencias'),
    path('tiposActividad/', views.tipos_actividad, name='tipos_actividad'),
    path('parametrosAreaPrograma/', views.parametros_area_programa, name='parametros_area_programa'),
    path('listarActividadesInconsistencias/', views.listar_actividades_inconsistencias, name='listar_actividades_inconsistencias'),
    path('listarActividadesAdmisionadas/', views.listar_actividades_admisionadas, name='listar_actividades_admisionadas'),
    path('listarActividadesCarga/<num_carga>', views.listar_actividades_carga, name='listar_actividades_carga'),
    # Grabar admisiones
    path('grabarAdmisionPrueba/', views.grabar_admision_prueba, name='grabar_admision_prueba'),
    path('consultarAdmisionesPrueba/', views.consultar_admisiones_prueba, name='consultar_admisiones_prueba'),
    # path('grabarAdmisiones/', views.grabar_admisiones),
    path('admisionarActividadesCarga/<id_carga>', views.admisionar_actividades_carga, name='admisionar_actividades_carga'),
    path('admisionarActividadIndividual/<id_actividad>/<pagina>', views.admisionar_actividad_individual, name='admisionar_actividad_individual'),
    path('eliminarActividadesInconsistenciaCarga/<id_carga>/<tipo_inconsistencia>', views.eliminar_actividades_inconsistencia_carga, name='eliminar_actividades_inconsistencia_carga'),
    path('eliminarActividadIndividual/<id_actividad>/<pagina>', views.eliminar_actividad_individual, name='eliminar_actividad_individual'),
    # Carga de Archivos
    path('cargarActividades/', views.cargar_actividades, name='cargar_actividades'),
    path('procesarCargueActividades/', views.procesarCargue, name='procesar_cargue_actividades'),
    path('informeCargas/', views.informe_cargas, name='informe_cargas'),
    path('verCarga/<id_carga>/<pagina>', views.ver_carga, name='ver_carga'),
    path('descargarArchivo/<nombre_archivo>', views.descargar_archivo, name='descargar_archivo'),
    path('exportarCargaExcel/<id_carga>/<tipo>', views.exportar_carga_excel, name='exportar_carga_excel'),
    # Administración
    path('administrador/', views.vista_administrador, name='vista_administrador'),
    path('cargarConfiguracionArranque/', views.cargar_configuracion_arranque, name='cargar_configuracion_arranque'),
]

