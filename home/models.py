from django.db import models
from django.contrib.auth.models import User
from zeus_mirror.models import Contrato, UnidadFuncional, CentroCosto, PuntoAtencion
from zeus_mirror.models import Sede, TipoServicio, Medico
import datetime
from datetime import timezone
# Create your models here.

class Admision(models.Model):
    id = models.AutoField(primary_key =True)
    documento_paciente = models.IntegerField()
    numero_estudio = models.IntegerField()
    json = models.JSONField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Admision - {self.id} - {self.documento_paciente} - {self.numero_estudio}'

class AreaPrograma(models.Model):
    id = models.AutoField(primary_key =True) 
    identificador = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    def __str__(self):
        return f'AreaPrograma - {self.id} - {self.identificador} - {self.nombre}' 

class Regional(models.Model):
    id = models.AutoField(primary_key =True) 
    regional = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    def __str__(self):
        return f'Regional - {self.id} - {self.regional}' 

class ContratoMarco(models.Model):
    id = models.AutoField(primary_key =True)
    numero = models.CharField(max_length = 50, unique=True)
    contrato_subsidiado = models.ForeignKey(Contrato, models.SET_NULL, blank=True,null=True, related_name='subsidado') 
    contrato_contributivo = models.ForeignKey(Contrato, models.SET_NULL, blank=True,null=True, related_name='contributivo') 
    observacion = models.CharField(max_length = 150, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'ContratoMarco- {self.id} - {self.numero} - {self.contrato_subsidiado} - {self.contrato_contributivo}'
       
class ParametrosAreaPrograma(models.Model):
    id = models.AutoField(primary_key =True)
    area_programa = models.ForeignKey(AreaPrograma, models.SET_NULL, blank=True,null=True) 
    regional = models.ForeignKey(Regional, models.SET_NULL, blank=True,null=True) 
    unidad_funcional = models.ForeignKey(UnidadFuncional, models.SET_NULL, blank=True,null=True) 
    punto_atencion = models.ForeignKey(PuntoAtencion, models.SET_NULL, blank=True,null=True) 
    centro_costo = models.ForeignKey(CentroCosto, models.SET_NULL, blank=True,null=True) 
    sede = models.ForeignKey(Sede, models.SET_NULL, blank=True,null=True, default=1) 
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'ParametrosAP - {self.id} - {self.regional} - {self.unidad_funcional} - {self.punto_atencion} - {self.centro_costo}' 
    
class Carga(models.Model):
    estados_carga = (
        ('eliminada',"Carga eliminada"),
        ('creada', "Carga creada"),
        ('procesando', "Carga en proceso"),
        ('procesada', "Carga procesada"), 
        ('admisionando', "Carga en proceso de creación de admisiones"), 
        ('cancelada', "Carga presentó errores durante su procesamiento"), 
    )
    id = models.AutoField(primary_key =True)
    usuario = models.ForeignKey(User, models.SET_NULL, blank=True,null=True)
    data = models.JSONField(blank=True,null=True)
    estado = models.CharField(max_length=20, default='creada', choices=estados_carga)
    cantidad_actividades = models.IntegerField(default = 0)
    cantidad_actividades_inconsistencias = models.IntegerField(default = 0)
    cantidad_actividades_ok = models.IntegerField(default = 0)
    cantidad_actividades_admisionadas = models.IntegerField(default = 0)
    tiempo_procesamiento = models.FloatField(default = 0)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self) -> str:
        return "Carga # {} ".format(self.id)
    
    def actualizar_info_actividades(self):
        actividades_carga = Actividad.objects.filter(carga = self)
        self.cantidad_actividades = actividades_carga.count()
        self.cantidad_actividades_ok = actividades_carga.filter(inconsistencias = None, admision = None).count()
        self.cantidad_actividades_admisionadas = actividades_carga.exclude(admision = None).filter(inconsistencias = None).count()
        self.cantidad_actividades_inconsistencias = self.cantidad_actividades - self.cantidad_actividades_ok - self.cantidad_actividades_admisionadas
    
class TipoActividad(models.Model):
    id = models.AutoField(primary_key =True)
    grupo = models.CharField(max_length= 10, blank=True,null=True)
    nombre = models.CharField(max_length= 150)
    cups = models.CharField(max_length= 10)
    responsable = models.CharField(max_length= 150, blank=True,null=True)
    diagnostico = models.CharField(max_length= 10, blank=True,null=True)
    finalidad = models.CharField(max_length= 50, blank=True,null=True)
    fuente = models.CharField(max_length= 50 ,blank=True,null=True)
    observacion = models.CharField(max_length= 150, blank=True,null=True)
    entrega = models.CharField(max_length= 150, blank=True,null=True)
    contrato = models.ForeignKey(ContratoMarco, models.SET_NULL, blank=True,null=True)
    tipo_servicio = models.ForeignKey(TipoServicio, models.SET_NULL, blank=True,null=True) #fuetnes tips # VALIDAR
    area = models.ForeignKey(AreaPrograma, models.SET_NULL, blank=True,null=True) 
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'TipoActividad - {self.id} - {self.nombre} - {self.cups} - {self.diagnostico}'
    
class Actividad(models.Model):
    
    id = models.AutoField(primary_key =True)
    tipo_fuente = models.CharField(max_length= 10)
    admision = models.ForeignKey(Admision, models.SET_NULL, blank=True,null=True)
    identificador = models.CharField(max_length= 150) 
    regional = models.CharField(max_length= 150)
    fecha_servicio = models.DateField()
    nombre_actividad = models.CharField(max_length= 250)
    tipo_actividad = models.ForeignKey(TipoActividad, models.SET_NULL, blank=True,null=True) 
    diagnostico_p = models.CharField(max_length= 10, default= "")
    diagnostico_1 = models.CharField(max_length= 10, default= "")
    diagnostico_2 = models.CharField(max_length= 10, default= "")
    diagnostico_3 = models.CharField(max_length= 10, default= "")
    tipo_documento = models.CharField(max_length= 10, default="CC")
    documento_paciente = models.CharField(max_length= 50)
    nombre_paciente = models.CharField(max_length= 50)
    parametros_programa =  models.ForeignKey(ParametrosAreaPrograma, models.SET_NULL, blank=True,null=True) 
    carga =  models.ForeignKey(Carga, models.SET_NULL, blank=True,null=True) 
    inconsistencias = models.CharField(max_length= 500, null=True, blank=True)
    medico = models.ForeignKey(Medico, models.SET_NULL, blank=True,null=True) 
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Actividad - {self.id} - {self.fecha_servicio} - {self.nombre_actividad}' 

class TokenApiZeus(models.Model):
    vigencia = 1

    id = models.AutoField(primary_key =True)
    token = models.CharField(max_length=250)
    vigente = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self) -> str:
        return "Token # {} ".format(self.id)
    
    def validar_vencimiento(self):
        print("Validar vencimiento: ", datetime.datetime.today(), self.updated_at)
        dias_uso = (datetime.date.today() - self.updated_at.date()).days
        print("DÍAS TOKEN:", dias_uso)
        if dias_uso > self.vigencia: # Validar si No está vigente
            self.vigente = False 
            self.save()

        




