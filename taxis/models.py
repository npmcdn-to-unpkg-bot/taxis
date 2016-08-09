from django.conf import settings
from django.db import models
from django.db.models import Q

from django.contrib.auth.models import User


# Create your models here.

class Taxista(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.user.username


class Propietario(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.user.username


class Administrador(models.Model):
    user = models.OneToOneField(User, on_delete=models.PROTECT)

    def __str__(self):
        return self.user.username


class TaxiManager(models.Manager):
    def get_mis_taxis(self, user):
        qs1 = Taxi.objects.filter(
            Q(propietario__user=user) |
            Q(conductor__user=user) |
            Q(administrador__user=user)
        ).distinct()
        return qs1



class Taxi(models.Model):
    placa = models.CharField(max_length=10)
    conductor = models.OneToOneField(Taxista, on_delete=models.PROTECT, null=True)
    propietario = models.ForeignKey(Propietario, on_delete=models.PROTECT, related_name="propietario")
    administrador = models.ForeignKey(Administrador, on_delete=models.PROTECT, related_name="administrador")

    def es_conductor(self, user):
        return self.conductor.user == user

    def es_administrador(self, user):
        return self.administrador.user == user

    def es_propietario(self, user):
        return self.propietario.user == user

    def natural_key(self):
        return self.placa

    objects = TaxiManager()

    def __str__(self):
        return self.placa
