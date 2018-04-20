from django.contrib import admin
from . import models

# Register your models here.
admin.site.register(models.Attribute)
admin.site.register(models.DataSourceType)
admin.site.register(models.Factoid)
admin.site.register(models.Goal)
admin.site.register(models.Metric)
admin.site.register(models.QualityModel)
