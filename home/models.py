from django.db import models

# Create your models here.

class TipoActividad(models.Model):
    id = models.AutoField(primary_key =True)
    grupo = models.CharField(max_length= 150)
    nombre = models.CharField(max_length= 150)
    cups = models.CharField(max_length= 10)
    responsable = models.CharField(max_length= 150)
    diagnostico = models.CharField(max_length= 10)
    finalidad = models.CharField(max_length= 50)
    fuente = models.CharField(max_length= 50)
    observacion = models.CharField(max_length= 150)
    entrega = models.CharField(max_length= 150)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Actividad - {self.id} - {self.nombre} - {self.cups} - {self.diagnostico}'
    


# class Admision(models.Model):
#     id = models.AutoField(primary_key =True)
#     autoid = models.IntegerField() # lo consultó con el documento del afiliado al endpoint
#     cod_entidad = models.CharField(max_length=20) # CONTRATO ?Definido dependiedo de la actividad
#     fecha_ing = models.DateField()
#     cod_medico = models.IntegerField()
#     nro_factura = models.IntegerField()
#     obs = models.TextField(max_length =  200)
#     cod_usuario = models.CharField(max_length= 20)
#     nom_usuario = models.CharField(max_length= 50)
#     contrato = models.IntegerField()
#     usuario_estado_res = models.CharField(max_length= 50)
#     codigo_servicio =  models.IntegerField()
#     ufuncional = models.IntegerField()
#     embarazo = models.CharField(max_length= 10)
#     id_sede = models.IntegerField()
#     punto_atencion = models.IntegerField()
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     def __str__(self):
#         return f'Admision - {self.id} - {self.autoid} - {self.cod_usuario} - {self.nom_usuario}'


# class Servicios(models.Model):
#     id = models.AutoField(primary_key =True)
#     admision = models.ForeignKey(Admision, models.SET_NULL, blank=True,null=True)
#     autoid = models.IntegerField()
#     fuente_tips = models.IntegerField()
#     num_servicio = models.IntegerField()
#     cod_servicio = models.CharField(max_length= 20)
#     fecha_servicio = models.DateField()
#     descripcion = models.TextField(max_length =  200)
#     cantidad = models.IntegerField()
#     vlr_servicio = models.FloatField()
#     total = models.FloatField()
#     tipo_diag = models.IntegerField()
#     cod_diap = models.CharField(max_length= 20)
#     cod_diagn1 = models.CharField(max_length= 20)
#     cod_diagn2 = models.CharField(max_length= 20)
#     cod_diagn2 = models.CharField(max_length= 20)
#     ccosto = models.CharField(max_length= 20)
#     ufuncional = models.IntegerField()
#     usuario = models.CharField(max_length= 20)
#     tipoitem = models.CharField(max_length= 20)
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     def __str__(self):
#         return f'Servicio - {self.id} - {self.cod_servicio} - {self.descripcion} - {self.cod_diap}'
    



# class NotaTecnica(models.Model):
#     id = models.AutoField(primary_key =True)
#     cups = models.CharField(max_length= 10)
#     cups = models.CharField(max_length= 10)
#     cups = models.CharField(max_length= 10)
#     cups = models.CharField(max_length= 10)
    


# class Parametros(models.Model):
#     id = models.AutoField(primary_key =True)
#     nombre = models.CharField(max_length= 20)
#     tipo = models.CharField(max_length= 20)
#     valor = models.CharField(max_length= 20)
#     created_at = models.DateTimeField(auto_now_add = True)
#     updated_at = models.DateTimeField(auto_now = True)

#     def __str__(self):
#         return f'Parametro - {self.id} - {self.nombre} - {self.tipo} - {self.valor}'



    



