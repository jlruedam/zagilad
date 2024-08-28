from django.contrib import admin
from home import models
# Register your models here.



class AdmisionAdmin(admin.ModelAdmin):
    pass

class AreaProgramaAdmin(admin.ModelAdmin):
    pass

class RegionalAdmin(admin.ModelAdmin):
    pass

class ContratoMarcoAdmin(admin.ModelAdmin):
    pass

class ParametrosAreaProgramaAdmin(admin.ModelAdmin):
    pass

class TipoActividadAdmin(admin.ModelAdmin):
    pass

class ActividadAdmin(admin.ModelAdmin):
    pass

class ColaboradorAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.Admision, AdmisionAdmin)
admin.site.register(models.AreaPrograma, AreaProgramaAdmin)
admin.site.register(models.Regional, RegionalAdmin)
admin.site.register(models.ContratoMarco, ContratoMarcoAdmin)
admin.site.register(models.ParametrosAreaPrograma, ParametrosAreaProgramaAdmin)
admin.site.register(models.TipoActividad, TipoActividadAdmin)
admin.site.register(models.Actividad, ActividadAdmin)
admin.site.register(models.Colaborador, ColaboradorAdmin)

