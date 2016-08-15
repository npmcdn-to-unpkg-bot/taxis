from decimal import Decimal
from django.core.validators import MinValueValidator
from django.utils import timezone

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
    ('3', 'Recibido - Admin'),
    ('4', 'Recibido - Prop'),
    ('5', 'Aceptada - Admin'),
    ('6', 'Aceptada - Prop'),
    ('7', 'Rechazada'),
)

def entrega_upload_to(instance, filename):
    id_user = instance.conductor.user.id
    basename, file_extention = filename.split(".")
    new_filename = "%s_%s.%s" % (instance.id, basename, file_extention)
    return "user/entrega/%s/%s" % (id_user, new_filename)

class EntregaoManager(models.Manager):
    def get_queryset(self):
        return super().get_queryset().order_by("-fecha")

    def get_mis_entregas(self, user):
        return Entrega.objects.filter(conductor=user)

    def get_mis_entregas_administrados(self, user):
        return Entrega.objects.filter(
            ~Q(conductor=user) &
            ~Q(taxi__propietario__user=user) &
            Q(taxi__administrador__user=user)
        )

    def get_mis_entregas_propios(self, user):
        return Entrega.objects.filter(
            ~Q(conductor=user) &
            Q(taxi__propietario__user=user) &
            ~Q(taxi__administrador__user=user)
        )

    def get_mis_entregas_como_conductor(self, user):
        mis_taxis = Taxi.objects.get_mis_taxis(user)
        return Entrega.objects.filter(taxi__in=mis_taxis)


class Entrega(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    conductor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="conductor_entrega")
    taxi = models.ForeignKey(Taxi, on_delete=models.PROTECT)

    actual_poseedor = models.ForeignKey(User, on_delete=models.PROTECT, related_name="usuario_tiene_entrega")
    token = models.PositiveSmallIntegerField(null=True, blank=True)
    fecha = models.DateField(default=timezone.now)

    imagen = models.ImageField(blank=True, upload_to=entrega_upload_to)

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

    def get_es_mi_entrega(self, user):
        return self.conductor == user

    def get_es_mi_entrega_administrado(self, user):
        es_administrador = self.taxi.es_administrador(user)
        es_propietario = self.taxi.es_propietario(user)
        if es_administrador and not es_propietario:
            return True
        return False

    def get_es_mi_entrega_propietario(self, user):
        return self.taxi.es_propietario(user)


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
    entrega = models.ForeignKey(Entrega, on_delete=models.CASCADE, related_name="conceptos")
    tipo = models.ForeignKey(ConceptoTipo, on_delete=models.PROTECT,related_name="conceptos")
    timespam_creation = models.DateTimeField(auto_now_add=True, auto_now=False)
    timespam_update = models.DateTimeField(auto_now_add=False, auto_now=True)
    descripcion = models.TextField(max_length=200, blank=True, null=True)
    fecha = models.DateField(default=timezone.now)
    imagen = models.ImageField(blank=True, null=True)
    valor = models.DecimalField(max_digits=10, decimal_places=2, default=0,validators=[MinValueValidator(Decimal('0.01'))])

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
