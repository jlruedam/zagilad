from django.db import models
from django.contrib.auth.models import User
from zeus_mirror.models import Contrato, UnidadFuncional, CentroCosto, PuntoAtencion, Sede, TipoServicio
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
    
class Colaborador(models.Model):
    id = models.AutoField(primary_key =True)
    usuario = models.ForeignKey(User, models.SET_NULL, blank=True,null=True)
    identificacion = models.CharField(max_length = 20, unique = True)
    nombre = models.CharField(max_length = 100)
    cargo = models.CharField(max_length = 100)
    email = models.CharField(max_length = 150, blank=True,null=True)
    is_active = models.BooleanField(default = False)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    class meta:
        verbose_name="Colaborador"
        verbose_name_plural="Colaboradores"
        db_table="colaborador"
        ordering=["id","identificacion","nombre"]

    def __str__(self) -> str:
        return "{} - {}".format(self.identificacion,self.nombre)



class Carga(models.Model):
    estados_carga = (
        (0, 'eliminada'),
        (1, 'creada'),
        (2, 'procesada')
    )
    id = models.AutoField(primary_key =True)
    usuario = models.ForeignKey(User, models.SET_NULL, blank=True,null=True)
    data = models.JSONField(blank=True,null=True)
    estado = models.CharField(max_length=1, default=1, choices=estados_carga)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)


    def __str__(self) -> str:
        return "Carga # {} ".format(self.id)


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
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Actividad - {self.id} - {self.fecha_servicio} - {self.nombre_actividad}' 





# parametros_generales= {
#     "codigo_medico":1,
#     "id_medico": "1047394846",
#     "cod_usuario":"1047394846",
#     "nom_usuario": "1047394846",
# }


