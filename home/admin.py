from django.contrib import admin
from home import models
# Register your models here.

class TipoActividadAdmin(admin.ModelAdmin):
    pass


admin.site.register(models.TipoActividad, TipoActividadAdmin)
