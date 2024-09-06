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
    # Grabar adminsiones
    path('grabarAdmisionPrueba/', views.grabar_admision_prueba),
    path('grabarAdmisiones/', views.grabar_admisiones),
    # Carga de Archivos
    path('cargarActividades/', views.cargar_actividades),
    path('procesarCargueActividades/', views.procesarCargue),
    path('informeCargas/', views.informe_cargas),
    path('verCarga/<id_carga>', views.ver_carga),
    path('ejecutarCarga/<id_carga>', views.ejecutar_carga),
    # Administración
    path('administrador/', views.vista_administrador),
    path('cargarConfiguracionArranque/', views.cargar_configuracion_arranque),
]

