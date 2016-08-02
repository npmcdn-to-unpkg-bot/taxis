from django.db.models.signals import post_save, pre_delete
from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q, Value, CharField

from taxis.models import Taxi, Taxista

from django.contrib.auth.models import User

# Create your models here.
STATUS_CHOICES = (
    ('1', 'Iniciada'),
    ('2', 'Enviada'),
    ('3', 'En Revición'),
    ('4', 'Aceptada'),
    ('5', 'Rechazada'),
)

class EntregaoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("-fecha")

    def get_mis_entregas(self,user):
        mis_taxis = Taxi.objects.get_mis_taxis(user)
        return Entrega.objects.filter(taxi__in=mis_taxis)

    def get_mis_entregas_como_conductor(self,user):
        mis_taxis = Taxi.objects.get_mis_taxis(user)
        return Entrega.objects.filter(taxi__in=mis_taxis)

class Entrega(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    taxi = models.ForeignKey(Taxi, on_delete=models.PROTECT)

    actual_poseedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="usuario_tiene_entrega")
    token = models.CharField(max_length=6)
    fecha = models.DateField()

    timespam_creation = models.DateTimeField(auto_now_add=True, auto_now=False)
    timespam_update = models.DateTimeField(auto_now_add=False, auto_now=True)

    status = models.CharField(max_length=1, choices=STATUS_CHOICES, default="1")
    total_ingreso = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_gasto = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    objects = EntregaoManager()

    def __str__(self):
        return "%s - %s" % (self.fecha, self.taxi.placa)

    def get_absolute_url(self):
        return reverse("entregas:entrega-detail", kwargs={"pk": self.pk})


class ConceptoTipo(models.Model):
    nombre = models.CharField(max_length=100)
    ingreso = models.BooleanField(default=True)
    descripcion = models.TextField(max_length=200, blank=True, null=True)

    def __str__(self):
        return self.nombre



class ConceptoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("fecha")


class Concepto(models.Model):
    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE)
    tipo = models.ForeignKey(ConceptoTipo, on_delete=models.PROTECT)
    timespam_creation = models.DateTimeField(auto_now_add=True, auto_now=False)
    timespam_update = models.DateTimeField(auto_now_add=False, auto_now=True)
    descripcion = models.TextField(max_length=200, blank=True, null=True)
    fecha = models.DateField()
    imagen = models.ImageField(blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    objects = ConceptoManager()

    def __str__(self):
        return "%s - %s" % (self.fecha, self.tipo)

def do_total_receiver(sender, instance, *args, **kwargs):
    entrega = instance.entrega
    if instance.tipo.ingreso:
        entrega.total_ingreso += instance.valor
    else:
        entrega.total_gasto += instance.valor
    entrega.total = entrega.total_ingreso - entrega.total_gasto
    entrega.save()

def do_total_delete_receiver(sender, instance, *args, **kwargs):
    entrega = instance.entrega
    if instance.tipo.ingreso:
        entrega.total_ingreso -= instance.valor
    else:
        entrega.total_gasto -= instance.valor
    entrega.total = entrega.total_ingreso - entrega.total_gasto
    entrega.save()

post_save.connect(do_total_receiver, sender=Concepto)
pre_delete.connect(do_total_delete_receiver, sender=Concepto)
