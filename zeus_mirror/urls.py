from django.contrib import admin
from django.urls import path
from zeus_mirror import views

urlpatterns = [
    path('consultasZeus/', views.consultas_zeus),
    path('consultarCodigosEmpresa/', views.consultar_codigos_empresas),
    path('consultarDatosPaciente/', views.consultar_datos_paciente),
    path('consultarMedicos/', views.consultar_medicos),
    path('consultarUsuariosZeus/', views.consultar_usuarios_zeus),
    path('listarTiposServicios/', views.listar_tipos_servicios),
    path('listarViasIngreso/', views.listar_vias_ingreso),
    path('listarCasusasExternas/', views.listar_causas_externas),
    path('listarUnidadesFuncionales/', views.listar_unidades_funcionales),
    path('listarSerialesSedes/', views.listar_seriales_sedes),
    path('listarPuntosAtencion/', views.listar_puntos_atencion),
    path('listarTiposDiagnosticos/', views.listar_tipos_diagnosticos),
    path('listarFinalidades/', views.listar_finalidades),
    path('listarCentrosCostos/', views.listar_centros_costos),
    path('listarEstratos/', views.listar_estratos),
    path('listarContratos/', views.listar_contratos),

]
