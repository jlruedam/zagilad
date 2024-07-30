"""
URL configuration for inzeusagilad project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from home import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', views.index),
    path('grabarAdmisionPrueba/', views.grabar_admision_prueba),
    path('consultarCodigosEmpresa/', views.consultar_codigos_empresas),
    path('consultarDatosPaciente/', views.consultar_datos_paciente),
    path('consultarMedicos/', views.consultar_medicos),
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


]
