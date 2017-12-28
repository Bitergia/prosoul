from django.db import models
from django.contrib.auth.models import User


class MeditorModel(models.Model):
    """ Basic metadata for Meditor objects """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    created_by = models.ForeignKey(User, null=True, on_delete=models.CASCADE)

    class Meta:
        abstract = True


class DataSourceType(MeditorModel):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Metric(MeditorModel):
    mclass = models.CharField(max_length=200)
    name = models.CharField(max_length=200)

    data_source_type = models.ForeignKey(DataSourceType, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('mclass', 'name')

    def __str__(self):
        return self.data_source_type.name + " " + self.mclass + " " + self.name


class Factoid(MeditorModel):
    name = models.CharField(max_length=200, unique=True)

    def __str__(self):
        return self.name


class Attribute(MeditorModel):
    name = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=4096, null=True)
    # Relations
    metrics = models.ManyToManyField(Metric)
    subattributes = models.ManyToManyField("Attribute", blank=True)

    def __str__(self):
        return self.name


class Goal(MeditorModel):
    name = models.CharField(max_length=200, unique=True)
    # Relations
    attributes = models.ManyToManyField(Attribute)
    subgoals = models.ManyToManyField("Goal", blank=True)

    def __str__(self):
        return self.name


class QualityModel(MeditorModel):
    """ Quality Model (maturity, Health ...)"""
    name = models.CharField(max_length=200, unique=True)
    # Relations
    goals = models.ManyToManyField("Goal")

    def __str__(self):
        return self.name
