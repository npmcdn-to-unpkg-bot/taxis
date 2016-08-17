import datetime
import json
import random

from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView, DeleteView
from django.views.generic.base import View
from django.views.generic.edit import CreateView

from taxis.models import Taxi,Portero
from users.mixin import LoginRequiredMixin
from .forms import EntregaForm, ConceptoForm, EntregaFormImagen
from .models import Entrega, Concepto


class EntregaUpdateAtributos(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        id_ent = self.request.POST.get("id_ent")
        entrega = get_object_or_404(Entrega, id=id_ent)
        if self.request.is_ajax():
            current_user = self.request.user
            new_token = random.randint(10000, 99999)

            if current_user.is_authenticated():

                if request.POST.get("tipo_update") == "validar_token":
                    token = request.POST.get("num_token")

                    if entrega.token == int(token):
                        entrega.actual_poseedor = current_user

                        if entrega.taxi.es_administrador(current_user):
                            entrega.status = 3
                            entrega.token = new_token
                            entrega.save()

                        if entrega.taxi.es_propietario(current_user):
                            entrega.status = 4
                            entrega.token = new_token
                            entrega.save()

                        if Portero.objects.filter(user=current_user).exists():
                            entrega.status = 7
                            entrega.token = new_token
                            entrega.save()

                if request.POST.get("tipo_update") == "siguiente_estado":

                    if entrega.get_es_mi_entrega(current_user):
                        if entrega.status == "1":
                            token = new_token
                            entrega.token = token
                            entrega.status = 2
                            entrega.save()

                    if entrega.get_es_mi_entrega_administrado(current_user):
                        if entrega.actual_poseedor == current_user:
                            token = new_token
                            entrega.token = token
                            entrega.status = 5
                            entrega.save()

                    if entrega.get_es_mi_entrega_propietario(current_user):
                        if entrega.actual_poseedor == current_user:
                            entrega.status = 6
                            entrega.save()

            return JsonResponse({"result": "Entrega Aceptada"})
        else:
            form = EntregaFormImagen(request.POST, request.FILES)
            form.instance = entrega
            if form.is_valid():
                # file is saved
                form.save()
            else:
                form = EntregaFormImagen()
                return render(request, entrega.get_absolute_url(), {'image_entrega': form})
        return redirect(entrega)


class EntregaListView(LoginRequiredMixin, View):
    model = Entrega
    template_name = "entregas/entrega_list.html"

    def get(self, request, *args, **kwargs):
        if self.request.is_ajax():
            json_list_entregas = []
            response = {}
            tipo_lista = self.request.GET.get("tipo")
            fecha_ultima_actualizacion_lista_cliente = self.request.GET.get("fecha_ultima_actualizacion")
            fecha_ultima_actualizacion_lista_servidor = '-1'
            context = ''
            actualizar = False
            usuario=self.request.user

            try:

                if tipo_lista == "mis_entregas":
                    fecha_ultima_actualizacion_lista_servidor = str(
                        Entrega.objects.get_mis_entregas(usuario).select_related("taxi").latest(
                            "timespam_update").timespam_update)
                    if fecha_ultima_actualizacion_lista_servidor != fecha_ultima_actualizacion_lista_cliente:
                        context = Entrega.objects.get_mis_entregas(self.request.user).select_related("taxi")
                        actualizar = True

                if tipo_lista == "mis_administrados":
                    fecha_ultima_actualizacion_lista_servidor = str(
                        Entrega.objects.get_mis_entregas_administrados(usuario).select_related("taxi").latest(
                            "timespam_update").timespam_update)
                    if fecha_ultima_actualizacion_lista_servidor != fecha_ultima_actualizacion_lista_cliente:
                        context = Entrega.objects.get_mis_entregas_administrados(self.request.user).select_related(
                            "taxi")
                        actualizar = True

                if tipo_lista == "mis_propios":
                    fecha_ultima_actualizacion_lista_servidor = str(
                        Entrega.objects.get_mis_entregas_propios(usuario).select_related("taxi").latest(
                            "timespam_update").timespam_update)

                    if fecha_ultima_actualizacion_lista_servidor != fecha_ultima_actualizacion_lista_cliente:
                        context = Entrega.objects.get_mis_entregas_propios(self.request.user).select_related("taxi")
                        actualizar = True

                if Portero.objects.filter(user=usuario).exists():
                    if tipo_lista == "portero":
                        fecha_ultima_actualizacion_lista_servidor = str(
                            Entrega.objects.filter(
                                Q(status=2) |
                                Q(status=7)
                            ).latest("timespam_update").timespam_update)
                        if fecha_ultima_actualizacion_lista_servidor != fecha_ultima_actualizacion_lista_cliente:
                            context = Entrega.objects.filter(
                                Q(status=2) |
                                Q(status=7)
                            ).select_related("taxi")
                            actualizar = True

                if actualizar:
                    for x in context:
                        object_json = {
                            "pk": x.id,
                            "entrega": "%s - (%s)" % (x.fecha.strftime("%m/%Y/%d"), x.taxi.placa),
                            "total": str(x.total),
                            "status": x.get_status_display(),
                            "url": x.get_absolute_url()
                        }
                        json_list_entregas.append(object_json)
            except:
                actualizar = False

            response = {
                "fecha_ultima_actualizacion": fecha_ultima_actualizacion_lista_servidor,
                "entregas": json_list_entregas,
            }

            return JsonResponse(json.dumps(response), safe=False)

        return render(request, self.template_name)


class EntregaDetailView(LoginRequiredMixin, DetailView):
    model = Entrega

    def get_context_data(self, **kwargs):
        new_concepto = ConceptoForm
        image_entrega = EntregaFormImagen
        contexto = super().get_context_data(**kwargs)
        contexto["form_new_concepto"] = new_concepto
        contexto["image_entrega"] = image_entrega
        return contexto

    def get(self, request, *args, **kwargs):

        if self.request.is_ajax():
            current_user = self.request.user
            ent_id = self.request.GET.get("ent_id")

            fecha_ultimaVersion_reacjs = self.request.GET.get("ultimo_update_entrega_fecha")
            fecha_ultimaVersion_db = str(get_object_or_404(Entrega, id=ent_id).timespam_update)

            if fecha_ultimaVersion_reacjs == fecha_ultimaVersion_db:
                return JsonResponse(json.dumps({"ultimo_update_entrega_fecha": fecha_ultimaVersion_db}), safe=False)
            else:
                entrega = get_object_or_404(
                    Entrega.objects.select_related('taxi', 'conductor', 'actual_poseedor').prefetch_related('conceptos')
                    , id=ent_id)

                Entrega.objects.select_related(None)
                Entrega.objects.prefetch_related(None)

                entrega_editable = False  # listo
                mostrar_boton_aceptar = False
                mostrar_token = False  # listo
                pedit_token = False  # listo
                mostrar_quien_tiene_entrega = False  # listo
                siguiente_estado = 0

                if Portero.objects.filter(user=current_user).exists():
                    if entrega.status == "2":
                        pedit_token = True
                        siguiente_estado = 7

                    if entrega.status == "7":
                        mostrar_token = True

                if entrega.get_es_mi_entrega(current_user):
                    if entrega.status == "1":
                        mostrar_boton_aceptar = True
                        siguiente_estado = 2
                        entrega_editable = True

                    if entrega.status == "2":
                        mostrar_token = True


                if entrega.get_es_mi_entrega_administrado(current_user):
                    mostrar_quien_tiene_entrega = True

                    if entrega.status == "7":
                        pedit_token = True

                    if entrega.status == "5":
                        mostrar_token = True

                    if entrega.status == "2":
                        pedit_token = True
                        siguiente_estado = 3

                    if entrega.status == "3":
                        siguiente_estado = 5
                        mostrar_boton_aceptar = True
                        if entrega.user == current_user:
                            entrega_editable = True

                if entrega.get_es_mi_entrega_propietario(current_user):
                    mostrar_quien_tiene_entrega = True

                    if entrega.status == "7":
                        pedit_token = True

                    if entrega.status == "2":
                        pedit_token = True
                        siguiente_estado = 4

                    if entrega.status == "5":
                        pedit_token = True
                        siguiente_estado = 4

                    if entrega.status == "4":
                        siguiente_estado = 6
                        mostrar_boton_aceptar = True
                        if entrega.user == current_user:
                            entrega_editable = True


                json_list_conceptos = []
                for x in entrega.conceptos.all():
                    url_imagen = "-1"
                    if x.imagen:
                        url_imagen = x.imagen.url

                    object_json_list = {
                        "pk": x.id,
                        "tipo": x.tipo.nombre,
                        "es_ingreso": x.tipo.ingreso,
                        "fecha": x.fecha.strftime("%m/%Y/%d"),
                        "valor": str(x.valor),
                        "url_delete": reverse("entregas:concepto-delete"),
                        "url_imagen": url_imagen
                    }

                    json_list_conceptos.append(object_json_list)

                entrega_url_imagen = "-1"
                if entrega.imagen:
                    entrega_url_imagen=entrega.imagen.url

                object_json = {
                    "estado": entrega.get_status_display(),
                    "url_delete": reverse("entregas:entrega-delete"),
                    "url_estado_token": reverse("entregas:entrega-update-atributos"),
                    "taxi": entrega.taxi.placa,
                    "fecha": entrega.fecha.strftime("%m/%Y/%d"),
                    "conductor": entrega.conductor.get_full_name(),
                    "valor": str(entrega.total),
                    "gasto": str(entrega.total_gasto),
                    "ingreso": str(entrega.total_ingreso),
                    "token": str(entrega.token),
                    "persona_entrega": str(entrega.actual_poseedor.get_full_name()),
                    "entrega_editable": entrega_editable,
                    "mostrar_token": mostrar_token,
                    "pedit_token": pedit_token,
                    "mostrar_quien_tiene_entrega": mostrar_quien_tiene_entrega,
                    "siguiente_estado": siguiente_estado,
                    "mostrar_boton_aceptar": mostrar_boton_aceptar,
                    "conceptos": json_list_conceptos,
                    "ultimo_update_entrega_fecha": str(entrega.timespam_update),
                    "url_imagen": entrega_url_imagen

                }
                return JsonResponse(json.dumps(object_json), safe=False)

        return super().get(request, *args, **kwargs)


class EntregaCreateView(LoginRequiredMixin, CreateView):
    model = Entrega
    form_class = EntregaForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        qst = Taxi.objects.get_mis_taxis(user)
        form.fields["taxi"].queryset = qst
        if qst.count() == 1:
            form.fields["taxi"].initial = qst[0]
        return form

    def post(self, request, *args, **kwargs):
        if self.get_form().is_valid():
            self.get_form().save(commit=False)
            dia = int(request.POST.get("fecha_day"))
            mes = int(request.POST.get("fecha_month"))
            ano = int(request.POST.get("fecha_year"))
            fecha = datetime.datetime(year=ano, month=mes, day=dia)
            user = self.request.user
            taxi_id = request.POST.get("taxi")
            taxi = Taxi.objects.get(pk=taxi_id)
            entrega = Entrega(actual_poseedor=user, taxi=taxi, user=user, fecha=fecha, conductor=taxi.conductor.user)

            if taxi.es_administrador(user):
                entrega.status = 3

            if taxi.es_propietario(user):
                entrega.status = 4

            entrega.save()
            return redirect(entrega.get_absolute_url())
        return super(EntregaCreateView, self).post(request, *args, **kwargs)


class ConceptoCreateView(LoginRequiredMixin, CreateView):
    model = Concepto
    form_class = ConceptoForm

    def form_valid(self, form):
        instance = form.instance
        ent_id = form.data['entrega_id']
        entrega = get_object_or_404(Entrega, id=ent_id)
        instance.entrega = entrega
        self.success_url = entrega.get_absolute_url()
        return super().form_valid(form)


class ConceptoDeleteView(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        id_concepto = self.request.POST.get("id_concept")
        concepto = get_object_or_404(Concepto, id=id_concepto)
        entrega = concepto.entrega

        if request.user.is_authenticated():
            concepto.delete()

            if self.request.is_ajax():
                return JsonResponse({"prueba": "funciono"})

        return redirect(entrega)


class EntregaDeleteView(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        current_user = self.request.user
        id_ent = self.request.POST.get("id_ent")
        entrega = get_object_or_404(Entrega, id=id_ent)

        delete = False

        if entrega.get_es_mi_entrega(current_user):
            if entrega.status == "1":
                if entrega.user == current_user:
                    delete = True

        if entrega.get_es_mi_entrega_administrado(current_user):
            if entrega.status == "3":
                if entrega.user == current_user:
                    delete = True

        if entrega.get_es_mi_entrega_propietario(current_user):
            if entrega.status == "4":
                if entrega.user == current_user:
                    delete = True

        if delete:
            print("Eliminó Entrega")
            entrega.delete()
            if self.request.is_ajax():
                return JsonResponse({"prueba": "funciono"})

        return redirect(reverse("entregas:entrega-list"))
