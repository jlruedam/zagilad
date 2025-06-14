from django.db import models

# Create your models here.
class Contrato(models.Model):
    id = models.AutoField(primary_key =True)
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=150)
    empresa = models.CharField(max_length=150)
    fecha_inicial = models.CharField(max_length=50)
    fecha_final = models.CharField(max_length=50)
    observacion = models.CharField(max_length=2000)
    numero = models.CharField(max_length=50)
    id_sede = models.CharField(max_length=50)
    regimen = models.CharField(max_length=50)
    activo = models.SmallIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
   
    def __str__(self):
        return f'Contrato - {self.codigo} - {self.empresa} - {self.numero} - {self.regimen}'

class UnidadFuncional(models.Model):
    id = models.AutoField(primary_key =True)
    id_zeus = models.IntegerField()
    codigo = models.CharField(max_length=50)
    descripcion = models.CharField(max_length=150)
    id_sede = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    def __str__(self):
        return f'UnidadFuncional - {self.id_zeus} - {self.codigo} - {self.descripcion}'
    
class PuntoAtencion(models.Model):
    id = models.AutoField(primary_key =True)
    id_zeus = models.IntegerField()
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=150)
    nit = models.CharField(max_length=50)
    direccion = models.CharField(max_length=150)
    departamento = models.CharField(max_length=10)
    municipio = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'PuntoAtencion - {self.id} - {self.id_zeus} - {self.codigo} - {self.nombre}'
    
class CentroCosto(models.Model):
    id = models.AutoField(primary_key =True)
    codigo = models.CharField(max_length=50)
    nombre = models.CharField(max_length=150)
    tipo = models.CharField(max_length=2)
    stock = models.CharField(max_length=2)
    activo_zeus = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'CentroCosto - {self.id} - {self.codigo} - {self.nombre}'
    
class Sede(models.Model):
    id = models.AutoField(primary_key =True)
    id_zeus = models.IntegerField()
    nit = models.CharField(max_length=50)
    razon_social = models.CharField(max_length=150)
    codigo_eps = models.CharField(max_length=150)
    direccion = models.CharField(max_length=150)
    ciudad = models.CharField(max_length=50)
    departamento= models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Sede - {self.id} - {self.id_zeus} - {self.nit} - {self.razon_social}'
    
class TipoServicio(models.Model):
    id = models.AutoField(primary_key =True)
    fuente = models.IntegerField()
    id_zeus = models.IntegerField()
    nombre = models.CharField(max_length= 150)
    tipo = models.CharField(max_length= 150)
    tipo_servicio = models.CharField(max_length= 5)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'TipoServicio - {self.id} - {self.id_zeus} - {self.nombre} - {self.tipo}'
    
class Medico(models.Model):
    id = models.AutoField(primary_key =True)
    codigo = models.CharField(max_length= 50)
    documento = models.CharField(max_length= 50)
    nombre = models.CharField(max_length= 250)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)

    def __str__(self):
        return f'Medico - {self.id} - {self.codigo} - {self.documento} - {self.nombre}'

class Finalidad(models.Model):
    id = models.AutoField(primary_key =True)
    numero = models.CharField(max_length= 10)
    valor = models.CharField(max_length= 10)
    nombre = models.CharField(max_length= 10)
    desplegable = models.CharField(max_length= 200)
    created_at = models.DateTimeField(auto_now_add = True)
    updated_at = models.DateTimeField(auto_now = True)
    
    def __str__(self):
        return f'Finalidad - {self.numero} - {self.nombre} - {self.desplegable}'
