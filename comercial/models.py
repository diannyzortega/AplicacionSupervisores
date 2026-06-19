# comercial/models.py
from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    id_usuario = models.IntegerField(unique=True)
    nombre = models.CharField(max_length=150)
    id_rol = models.IntegerField()
    id_region = models.IntegerField()
    id_sucursal = models.IntegerField()

    def __str__(self):
        return f"{self.nombre} ({self.user.username})"

class Region(models.Model):
    id_region = models.IntegerField(unique=True)
    nombre_region = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_region

class Rol(models.Model):
    id_rol = models.IntegerField(unique=True)
    nombre_rol = models.CharField(max_length=100)

    def __str__(self):
        return self.nombre_rol

class Sucursal(models.Model):
    id_sucursal = models.IntegerField(unique=True)
    nombre_sucursal = models.CharField(max_length=100)
    id_region = models.IntegerField()

    def __str__(self):
        return self.nombre_sucursal

class Asesor(models.Model):
    id_asesor = models.CharField(max_length=100, primary_key=True)
    nombre_asesor = models.CharField(max_length=150)
    id_usuario = models.IntegerField(null=True, blank=True)
    maestra = models.CharField(max_length=100, blank=True, null=True, default='')
    maestra_rebanadoras = models.CharField(max_length=100, blank=True, null=True, default='')

    def __str__(self):
        return self.nombre_asesor

class Categoria(models.Model):
    id_categoria = models.IntegerField(primary_key=True)
    nombre_categoria = models.CharField(max_length=100)
    id_region = models.IntegerField(default=0)
    obj_activacion = models.IntegerField(default=0)
    tipo_obj_activacion = models.CharField(max_length=50, default='Porcentaje')
    obj_volumen = models.IntegerField(default=0)
    obj_profundidad = models.IntegerField(default=0)
    tipo_medida = models.CharField(max_length=20, choices=[('caja','Caja'),('kilo','Kilo'),('unidad','Unidad')], default='unidad')

    def __str__(self):
        return self.nombre_categoria

class AsesorCategoria(models.Model):
    id_asesor = models.CharField(max_length=100)
    id_categoria = models.IntegerField()
    obj_volumen = models.FloatField(default=0.0)
    obj_profundidad = models.FloatField(default=0.0)

    def __str__(self):
        return f"Asesor {self.id_asesor} - Cat {self.id_categoria}"

class SeguimientoDiario(models.Model):
    id_asesor = models.CharField(max_length=100)
    id_categoria = models.IntegerField()
    act_lleva = models.FloatField(default=0.0)
    vol_lleva = models.FloatField(default=0.0)
    prof_lleva = models.FloatField(default=0.0)

    def __str__(self):
        return f"Seguimiento: {self.id_asesor} - Cat {self.id_categoria}"

class PlanificacionSemanal(models.Model):
    class Meta:
        unique_together = (('fecha', 'supervisor'),)
    fecha = models.DateField()
    supervisor = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    sucursal = models.CharField(max_length=100)
    modalidad = models.CharField(max_length=100, blank=True, null=True)
    acompanamiento = models.CharField(max_length=10, blank=True, null=True)
    asesor = models.CharField(max_length=100, blank=True, null=True, default='')
    zona = models.CharField(max_length=100, blank=True, null=True, default='')
    clientes_actuales = models.IntegerField(default=0)
    clientes_captar = models.IntegerField(default=0)
    objetivo_principal = models.TextField(blank=True, null=True, default='')

    enfoque = models.TextField(blank=True, null=True, default='')
    auditoria_jamones = models.IntegerField(default=0)
    auditoria_quesos = models.IntegerField(default=0)
    monto_proyectado_cobro = models.FloatField(default=0.0)
    cajas_objetivo = models.FloatField(default=0.0)
    kilos_objetivo = models.FloatField(default=0.0)

    def __str__(self):
        return f"{self.fecha} - {self.supervisor}"

class ResultadosTarde(models.Model):
    fecha_cierre = models.DateField()
    supervisor = models.CharField(max_length=100)
    region = models.CharField(max_length=100)
    sucursal = models.CharField(max_length=100)
    total_clientes_dia = models.IntegerField(default=0)
    clts_a_captar = models.IntegerField(default=0)
    meta_cajas_matutina = models.FloatField(default=0.0)
    meta_kilos_matutina = models.FloatField(default=0.0)
    meta_cobranza_matutina = models.FloatField(default=0.0)
    cajas_reales = models.FloatField(default=0.0)
    kilos_reales = models.FloatField(default=0.0)
    monto_cobrado_real = models.FloatField(default=0.0)
    clientes_activados = models.IntegerField(default=0)
    clientes_apertura_nuevos = models.IntegerField(default=0)
    clts_visita_con_pop = models.IntegerField(default=0)
    clts_con_1_sku = models.IntegerField(default=0)
    clts_con_2_sku = models.IntegerField(default=0)
    clts_con_mas_3_sku = models.IntegerField(default=0)
    cumplio_pasos_visita = models.CharField(max_length=100, blank=True, null=True, default='')
    usa_catalogo = models.CharField(max_length=100, blank=True, null=True, default='')
    calidad_atencion = models.CharField(max_length=100, blank=True, null=True, default='')
    audito_jamon = models.CharField(max_length=100, blank=True, null=True, default='')
    obs_jamon_concurso = models.TextField(blank=True, null=True, default='')
    audito_queso = models.CharField(max_length=100, blank=True, null=True, default='')
    obs_queso_concurso = models.TextField(blank=True, null=True, default='')
    cumplimiento_plan = models.CharField(max_length=100, blank=True, null=True, default='')
    novedades_market = models.TextField(blank=True, null=True, default='')

    def __str__(self):
        return f"{self.fecha_cierre} - {self.supervisor}"

class RegistroDiario(models.Model):
    fecha = models.DateField()
    id_asesor = models.CharField(max_length=100)
    id_categoria = models.IntegerField()
    act_dia = models.FloatField(default=0.0)
    vol_dia = models.FloatField(default=0.0)
    prof_dia = models.FloatField(default=0.0)

    def __str__(self):
        return f"Registro: {self.fecha} - {self.id_asesor} - Cat {self.id_categoria}"
