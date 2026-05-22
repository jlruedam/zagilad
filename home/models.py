from django.db import models
from django.contrib.auth.models import User
from zeus_mirror.models import Contrato, UnidadFuncional, CentroCosto, PuntoAtencion
from zeus_mirror.models import Sede, TipoServicio, Medico, Finalidad
import datetime
from datetime import timezone

# Create your models here.


class Admision(models.Model):
    id = models.AutoField(primary_key=True)
    documento_paciente = models.IntegerField()
    numero_estudio = models.IntegerField()
    observacion = models.CharField(max_length=150, blank=True, null=True)
    json = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Admision_{self.id}_{self.documento_paciente}_{self.numero_estudio}"


class AreaPrograma(models.Model):
    id = models.AutoField(primary_key=True)
    identificador = models.CharField(max_length=10, unique=True)
    nombre = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"AreaPrograma_{self.id}_{self.identificador}_{self.nombre}"


class Regional(models.Model):
    id = models.AutoField(primary_key=True)
    regional = models.CharField(max_length=150)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Regional_{self.id}_{self.regional}"


class ContratoMarco(models.Model):
    id = models.AutoField(primary_key=True)
    numero = models.CharField(max_length=50, unique=True)
    contrato_subsidiado = models.ForeignKey(
        Contrato, models.SET_NULL, blank=True, null=True, related_name="subsidado"
    )
    contrato_contributivo = models.ForeignKey(
        Contrato, models.SET_NULL, blank=True, null=True, related_name="contributivo"
    )
    observacion = models.CharField(max_length=150, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ContratoMarco_{self.id}_{self.numero}_{self.contrato_subsidiado}_{self.contrato_contributivo}"


class ParametrosAreaPrograma(models.Model):
    id = models.AutoField(primary_key=True)
    area_programa = models.ForeignKey(
        AreaPrograma, models.SET_NULL, blank=True, null=True
    )
    regional = models.ForeignKey(Regional, models.SET_NULL, blank=True, null=True)
    unidad_funcional = models.ForeignKey(
        UnidadFuncional, models.SET_NULL, blank=True, null=True
    )
    punto_atencion = models.ForeignKey(
        PuntoAtencion, models.SET_NULL, blank=True, null=True
    )
    centro_costo = models.ForeignKey(
        CentroCosto, models.SET_NULL, blank=True, null=True
    )
    sede = models.ForeignKey(Sede, models.SET_NULL, blank=True, null=True, default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"ParametrosAP - {self.id} - {self.regional} - {self.unidad_funcional} - {self.punto_atencion} - {self.centro_costo}"


class Carga(models.Model):
    estados_carga = (
        ("eliminada", "Carga eliminada"),
        ("creada", "Carga creada"),
        ("procesando", "Carga en proceso"),
        ("procesada", "Carga procesada"),
        ("admisionando", "Carga en proceso de creación de admisiones"),
        ("cancelada", "Carga presentó errores durante su procesamiento"),
    )
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, models.SET_NULL, blank=True, null=True)
    data = models.JSONField(blank=True, null=True)
    estado = models.CharField(max_length=20, default="creada", choices=estados_carga)
    cantidad_actividades = models.IntegerField(default=0)
    cantidad_actividades_inconsistencias = models.IntegerField(default=0)
    cantidad_actividades_ok = models.IntegerField(default=0)
    cantidad_actividades_admisionadas = models.IntegerField(default=0)
    tiempo_procesamiento = models.FloatField(default=0)
    observacion = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return "Carga #{}-{}-{} ".format(self.id, self.estado, self.observacion)

    def actualizar_info_actividades(self):
        actividades_carga = Actividad.objects.filter(carga=self)
        self.cantidad_actividades = actividades_carga.count()
        self.cantidad_actividades_ok = actividades_carga.filter(
            inconsistencias=None, admision=None
        ).count()
        self.cantidad_actividades_admisionadas = (
            actividades_carga.exclude(admision=None)
            .filter(inconsistencias=None)
            .count()
        )
        self.cantidad_actividades_inconsistencias = (
            self.cantidad_actividades
            - self.cantidad_actividades_ok
            - self.cantidad_actividades_admisionadas
        )


class TipoActividad(models.Model):
    id = models.AutoField(primary_key=True)
    grupo = models.CharField(max_length=10, blank=True, null=True)
    nombre = models.CharField(max_length=150)
    cups = models.CharField(max_length=10)
    responsable = models.CharField(max_length=150, blank=True, null=True)
    diagnostico = models.CharField(max_length=10, blank=True, null=True)
    finalidad = models.CharField(max_length=50, blank=True, null=True)
    fuente = models.CharField(max_length=50, blank=True, null=True)
    observacion = models.CharField(max_length=150, blank=True, null=True)
    entrega = models.CharField(max_length=150, blank=True, null=True)
    contrato = models.ForeignKey(ContratoMarco, models.SET_NULL, blank=True, null=True)
    tipo_servicio = models.ForeignKey(TipoServicio, models.SET_NULL, blank=True, null=True)  # fuentes tips # VALIDAR
    area = models.ForeignKey(AreaPrograma, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"TipoActividad - {self.id} - {self.nombre} - {self.cups} - {self.diagnostico}"


class Actividad(models.Model):

    id = models.AutoField(primary_key=True)
    tipo_fuente = models.CharField(max_length=10,blank=True, default="")
    admision = models.ForeignKey(Admision, models.SET_NULL, blank=True, null=True)
    identificador = models.CharField(max_length=150, blank=True, null=True)
    regional = models.CharField(max_length=150)
    fecha_servicio = models.DateField()
    nombre_actividad = models.CharField(max_length=250)
    tipo_actividad = models.ForeignKey(TipoActividad, models.SET_NULL, blank=True, null=True)
    diagnostico_p = models.CharField(max_length=10, default="", blank=True, null=True)
    diagnostico_1 = models.CharField(max_length=10, default="", blank=True, null=True)
    diagnostico_2 = models.CharField(max_length=10, default="", blank=True, null=True)
    diagnostico_3 = models.CharField(max_length=10, default="", blank=True, null=True)
    tipo_documento = models.CharField(max_length=10, default="CC")
    documento_paciente = models.CharField(max_length=50)
    nombre_paciente = models.CharField(max_length=200)
    parametros_programa = models.ForeignKey(ParametrosAreaPrograma, models.SET_NULL, blank=True, null=True)
    carga = models.ForeignKey(Carga, models.SET_NULL, blank=True, null=True)
    finalidad = models.ForeignKey(Finalidad, models.SET_NULL, blank=True, null=True)
    inconsistencias = models.CharField(max_length=500, null=True, blank=True)
    documento_medico = models.CharField(max_length=50, blank=True, null=True)
    medico = models.ForeignKey(Medico, models.SET_NULL, blank=True, null=True)
    admisionada_otra_carga = models.BooleanField(default=False)
    datos_json = models.JSONField(blank=True, null=True)
    tipo_usuario = models.CharField(max_length=2, blank=True, null=True)
    contrato = models.ForeignKey(ContratoMarco, models.SET_NULL, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(
                fields=["carga", "admision"],
                name="act_carga_adm_idx",
            ),
            models.Index(
                fields=[
                    "documento_paciente",
                    "fecha_servicio",
                    "nombre_actividad",
                    "tipo_actividad",
                    "medico",
                    "admision",
                ],
                name="act_dup_adm_idx",
            ),
            models.Index(
                fields=[
                    "carga",
                    "documento_paciente",
                    "fecha_servicio",
                    "nombre_actividad",
                    "tipo_actividad",
                    "medico",
                ],
                name="act_dup_carga_idx",
            ),
        ]

    def __str__(self):
        return (
            f"Actividad - {self.id} - {self.fecha_servicio} - {self.nombre_actividad}"
        )


class TokenApiZeus(models.Model):
    vigencia = 1

    id = models.AutoField(primary_key=True)
    token = models.CharField(max_length=250)
    vigente = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return "Token # {} ".format(self.id)

    def validar_vencimiento(self):
        print("Validar vencimiento: ", datetime.datetime.today(), self.updated_at)
        dias_uso = (datetime.date.today() - self.updated_at.date()).days
        print("DÍAS TOKEN:", dias_uso)
        if dias_uso > self.vigencia:  # Validar si No está vigente
            self.vigente = False
            self.save()


class FuenteTipoUsuario(models.Model):
    """
    Configuración de una fuente externa SQL Server para resolver el tipo de
    usuario (régimen + tipo afiliado → código SIESA).

    Cada fila define una conexión, una tabla y el mapeo de las 3 columnas
    requeridas. Las fuentes activas se consultan en cascada ordenadas por
    `prioridad` (menor número primero).

    El password vive cifrado con Fernet en `password_encrypted`. Nunca se
    expone en texto plano fuera del proceso que lo consume.
    """

    ESTADO_OK = "ok"
    ESTADO_ERROR = "error"
    ESTADO_PENDIENTE = "pendiente"
    ESTADO_VALIDACION_CHOICES = (
        (ESTADO_OK, "OK"),
        (ESTADO_ERROR, "Error"),
        (ESTADO_PENDIENTE, "Pendiente"),
    )

    id = models.AutoField(primary_key=True)
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Identificador único (ej. MUTUAL_VIEW)",
    )
    descripcion = models.CharField(max_length=250, blank=True, default="")
    activa = models.BooleanField(default=True)
    prioridad = models.IntegerField(
        default=100,
        help_text="Menor número = mayor prioridad en la cascada",
    )

    servidor = models.CharField(max_length=200)
    base_datos = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text="Opcional si la tabla incluye DB.schema.tabla",
    )
    usuario = models.CharField(max_length=100)
    password_encrypted = models.TextField(
        help_text="Cifrado con Fernet — no editar manualmente"
    )
    driver = models.CharField(max_length=100, default="SQL Server")

    tabla = models.CharField(
        max_length=200,
        help_text="Nombre completo, ej: MUTUALSER.dbo.DL_MS_AFILIADO_VIEW_CLEAN",
    )
    campo_documento = models.CharField(max_length=100)
    campo_tipo_documento = models.CharField(
        max_length=100,
        blank=True,
        default="",
        help_text=(
            "Opcional. Columna del tipo de documento (CC/TI/RC/…). "
            "Si está configurada, la consulta filtra por documento + tipo doc."
        ),
    )
    campo_regimen = models.CharField(max_length=100)
    campo_tipo_afiliado = models.CharField(max_length=100)

    estado_validacion = models.CharField(
        max_length=20,
        default=ESTADO_PENDIENTE,
        choices=ESTADO_VALIDACION_CHOICES,
    )
    mensaje_validacion = models.TextField(blank=True, default="")
    ultima_validacion_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["prioridad", "nombre"]
        verbose_name = "Fuente de tipo de usuario"
        verbose_name_plural = "Fuentes de tipo de usuario"

    def __str__(self):
        return f"FuenteTipoUsuario - {self.nombre} (prio={self.prioridad}, activa={self.activa})"


class ReglaHomologacionSIESA(models.Model):
    """
    Regla `régimen + tipo_afiliado → código SIESA`.

    `fuente = NULL` → regla global aplicable a todas las fuentes.
    `fuente ≠ NULL` → override específico para esa fuente (toma precedencia
    sobre la global con el mismo (régimen, tipo)).

    `tipo_afiliado_codigo = '*'` → wildcard (cualquier tipo bajo ese régimen),
    útil para Subsidiado donde el tipo de afiliado no diferencia el SIESA.
    """

    id = models.AutoField(primary_key=True)
    fuente = models.ForeignKey(
        FuenteTipoUsuario,
        models.CASCADE,
        blank=True,
        null=True,
        help_text="NULL = regla global",
    )
    regimen = models.CharField(max_length=10)
    tipo_afiliado_codigo = models.CharField(
        max_length=10,
        help_text='Código corto. "*" = cualquier tipo bajo ese régimen',
    )
    codigo_siesa = models.CharField(max_length=10)
    descripcion = models.CharField(max_length=150, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fuente", "regimen", "tipo_afiliado_codigo"],
                name="uniq_regla_siesa_fuente_reg_tipo",
                condition=models.Q(fuente__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["regimen", "tipo_afiliado_codigo"],
                name="uniq_regla_siesa_global_reg_tipo",
                condition=models.Q(fuente__isnull=True),
            ),
        ]
        ordering = ["fuente_id", "regimen", "tipo_afiliado_codigo"]
        verbose_name = "Regla de homologación SIESA"
        verbose_name_plural = "Reglas de homologación SIESA"

    def __str__(self):
        scope = self.fuente.nombre if self.fuente_id else "GLOBAL"
        return f"{scope}: {self.regimen}+{self.tipo_afiliado_codigo} → {self.codigo_siesa}"


class NormalizacionTipoAfiliado(models.Model):
    """
    Mapeo `valor crudo → código corto` para el tipo de afiliado.

    Resuelve typos históricos (`'CABEZA DE FAMLIA'` → `'F'`) y normaliza los
    nombres largos del SQL a los códigos cortos que entiende la tabla de
    reglas SIESA.

    `fuente = NULL` → mapeo global. `fuente ≠ NULL` → override por fuente.
    """

    id = models.AutoField(primary_key=True)
    fuente = models.ForeignKey(
        FuenteTipoUsuario,
        models.CASCADE,
        blank=True,
        null=True,
        help_text="NULL = mapeo global",
    )
    valor_crudo = models.CharField(
        max_length=100,
        help_text="Tal cual lo devuelve la fuente",
    )
    codigo_normalizado = models.CharField(max_length=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["fuente", "valor_crudo"],
                name="uniq_normalizacion_fuente_valor",
                condition=models.Q(fuente__isnull=False),
            ),
            models.UniqueConstraint(
                fields=["valor_crudo"],
                name="uniq_normalizacion_global_valor",
                condition=models.Q(fuente__isnull=True),
            ),
        ]
        ordering = ["fuente_id", "valor_crudo"]
        verbose_name = "Normalización de tipo de afiliado"
        verbose_name_plural = "Normalizaciones de tipo de afiliado"

    def __str__(self):
        scope = self.fuente.nombre if self.fuente_id else "GLOBAL"
        return f"{scope}: '{self.valor_crudo}' → '{self.codigo_normalizado}'"
