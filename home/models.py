from django.db import models

# Create your models here.

class Contrato(models.Model):
    id = models.AutoField(primary_key =True)
    numero_contrato = models.IntegerField(blank=True,null=True, unique=True)
    nombre = models.CharField(max_length= 150)
    regimen = models.CharField(max_length= 150, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Contrato - {self.id}' 


class TipoActividad(models.Model):
    id = models.AutoField(primary_key =True)
    grupo = models.CharField(max_length= 150)
    nombre = models.CharField(max_length= 150)
    cups = models.CharField(max_length= 10)
    responsable = models.CharField(max_length= 150)
    diagnostico = models.CharField(max_length= 10, blank=True,null=True)
    finalidad = models.CharField(max_length= 50, blank=True,null=True)
    fuente = models.CharField(max_length= 50)
    observacion = models.CharField(max_length= 150)
    entrega = models.CharField(max_length= 150)
    contrato = models.ManyToManyField(Contrato, related_name='contratos') # https://www.youtube.com/watch?v=QBzsoQPgJQ8
    # numero_contrato = models.SmallIntegerField(blank=True,null=True)
    tipo_servicio = models.SmallIntegerField(blank=True,null=True) #fuetnes tips # VALIDAR
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'TipoActividad - {self.id} - {self.nombre} - {self.cups} - {self.diagnostico}'
    

class Admision(models.Model):
    id = models.AutoField(primary_key =True)
    autoid = models.IntegerField() # lo consultó con el documento del afiliado al endpoint
    cod_entidad = models.CharField(max_length=20) # CONTRATO ?Definido dependiedo de la actividad
    fecha_ing = models.DateField()
    cod_medico = models.IntegerField()
    nro_factura = models.IntegerField()
    obs = models.TextField(max_length =  200)
    cod_usuario = models.CharField(max_length= 20)
    nom_usuario = models.CharField(max_length= 50)
    contrato = models.IntegerField()
    usuario_estado_res = models.CharField(max_length= 50)
    codigo_servicio =  models.IntegerField()
    ufuncional = models.IntegerField()
    embarazo = models.CharField(max_length= 10)
    id_sede = models.IntegerField()
    punto_atencion = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Admision - {self.id} - {self.autoid} - {self.cod_usuario} - {self.nom_usuario}'
    
class Actividad(models.Model):
    id = models.AutoField(primary_key =True)
    identificador = models.CharField(max_length= 150, unique=True)
    tipo_fuente = models.CharField(max_length= 10)
    tipo_actividad = models.ForeignKey(TipoActividad, models.SET_NULL, blank=True,null=True)
    fecha_servicio = models.DateField()
    descripcion = models.CharField(max_length= 250)
    diagnostico_p = models.CharField(max_length= 10, default= "")
    diagnostico_1 = models.CharField(max_length= 10, default= "")
    diagnostico_2 = models.CharField(max_length= 10, default= "")
    diagnostico_3 = models.CharField(max_length= 10, default= "")
    tipo_documento = models.CharField(max_length= 10, default="CC")
    documento_paciente = models.CharField(max_length= 50)
    nombre_paciente = models.CharField(max_length= 50)
    embarazo = models.CharField(max_length= 150)
    sede = models.CharField(max_length= 150, blank=True,null=True) # VALIDAR
    unidad_funcional = models.CharField(max_length= 150, blank=True,null=True) # VALIDAR
    punto_atencion = models.CharField(max_length= 150, blank=True,null=True) # VALIDAR
    centro_costo = models.CharField(max_length= 150, blank=True,null=True) # VALIDAR
    admision = models.ForeignKey(Admision, models.SET_NULL, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Actividad - {self.id} - {self.identificador} - {self.tipo_fuente} - {self.tipo}' 
    
# class Parametros(models.Model):
#     id = models.AutoField(primary_key =True)
#     nombre = models.CharField(max_length= 20)
#     tipo = models.CharField(max_length= 20)
#     valor = models.CharField(max_length= 20)
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     def __str__(self):
#         return f'Parametro - {self.id} - {self.nombre} - {self.tipo} - {self.valor}'



    
parametros_generales= {
    "codigo_medico":1,
    "id_medico": "1047394846",
    "cod_usuario":"1047394846",
    "nom_usuario": "1047394846",
}


