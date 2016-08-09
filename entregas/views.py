import datetime
import random
import json

from django.core import serializers
from django.http import JsonResponse
from django.core.mail import send_mail
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.edit import CreateView
from django.views.generic.base import View

# Create your views here.
from .forms import EntregaForm, ConceptoForm
from .models import Entrega, Concepto, ConceptoTipo
from taxis.models import Taxi
from users.mixin import LoginRequiredMixin


class EntregaUpdateAtributos(LoginRequiredMixin, View):
    def post(self, request, *args, **kwargs):
        current_user = self.request.user

        if current_user.is_authenticated():
            id_ent = self.request.POST.get("id_ent")
            entrega = get_object_or_404(Entrega, id=id_ent)

            if request.POST.get("tipo_update") == "validar_token":
                token = request.POST.get("num_token")

                if entrega.token == int(token):
                    entrega.actual_poseedor = current_user

                    if entrega.taxi.es_administrador(current_user):
                        # entrega.status = 3
                        # entrega.token = random.randint(10000, 99999)
                        entrega.save()

                    if entrega.taxi.es_propietario(current_user):
                        # entrega.status = 4
                        # entrega.token = random.randint(10000, 99999)
                        entrega.save()

            if request.POST.get("tipo_update") == "siguiente_estado":

                if entrega.get_es_mi_entrega(current_user):
                    if entrega.status == "1":
                        # token = random.randint(10000, 99999)
                        # entrega.token = token
                        entrega.status = 2
                        entrega.save()

                if entrega.get_es_mi_entrega_administrado(current_user):
                    if entrega.actual_poseedor == current_user:
                        # token = random.randint(10000, 99999)
                        # entrega.token = token
                        entrega.status = 5
                        entrega.save()

                if entrega.get_es_mi_entrega_propietario(current_user):
                    if entrega.actual_poseedor == current_user:
                        entrega.status = 6
                        entrega.save()

        return redirect(entrega)


class EntregaListView(LoginRequiredMixin,View):
    model = Entrega
    template_name = "entregas/entrega_list.html"


    def get(self, request, *args, **kwargs):
        if self.request.is_ajax():
            json_object = []

            if self.request.GET.get("tipo") == "mis_entregas":
                context = Entrega.objects.get_mis_entregas(self.request.user)
                for x in context:
                    object_json = {
                        "pk":x.id,
                        "entrega": "%s - (%s)" %(x.fecha.strftime("%m/%Y/%d"),x.taxi.placa),
                        "total": str(x.total),
                        "status":x.get_status_display(),
                        "url":x.get_absolute_url()
                    }
                    json_object.append(object_json)
                # data = serializers.serialize("json",context,use_natural_foreign_keys=True)

            if self.request.GET.get("tipo") == "mis_administrados":
                context = Entrega.objects.get_mis_entregas_administrados(self.request.user)
                for x in context:
                    object_json = {
                        "pk": x.id,
                        "entrega": "%s - (%s)" % (x.fecha.strftime("%m/%Y/%d"), x.taxi.placa),
                        "total": str(x.total),
                        "status": x.get_status_display(),
                        "url": x.get_absolute_url()
                    }
                    json_object.append(object_json)
                    # data = serializers.serialize("json",context,use_natural_foreign_keys=True)

            if self.request.GET.get("tipo") == "mis_propios":
                context = Entrega.objects.get_mis_entregas_propios(self.request.user)
                for x in context:
                    object_json = {
                        "pk": x.id,
                        "entrega": "%s - (%s)" % (x.fecha.strftime("%m/%Y/%d"), x.taxi.placa),
                        "total": str(x.total),
                        "status": x.get_status_display(),
                        "url": x.get_absolute_url()
                    }
                    json_object.append(object_json)
                    # data = serializers.serialize("json",context,use_natural_foreign_keys=True)

            return JsonResponse(json.dumps(json_object), safe=False)
        send_mail(subject="pruebanueva", message="estamos probando 2", from_email="prueba@nuevo.fabgarsan.webfactional.com",
                  recipient_list=['fabio.garcia.sanchez@gmail.com'])
        print("Envio Correo")
        return render(request, self.template_name)




class EntregaDetailView(LoginRequiredMixin, DetailView):
    model = Entrega

    def get_context_data(self, **kwargs):
        new_concepto = ConceptoForm
        contexto = super().get_context_data(**kwargs)

        current_user = self.request.user

        entrega = contexto["object"]

        siguiente_estado = 0  # whe this is 0 the button to get the next stage will be disabled
        conceptos_eliminables = False
        mostrar_token = False
        mostrar_pedir_token = False
        mostrar_boton_aceptar = False
        mostrar_actual_poseedor = False

        if entrega.get_es_mi_entrega(current_user):
            if entrega.status == "1":
                mostrar_boton_aceptar = True
                siguiente_estado = 2
                conceptos_eliminables = True

            if entrega.status == "2":
                mostrar_token = True

            if entrega.status == "2":
                mostrar_token = True

        if entrega.get_es_mi_entrega_administrado(current_user):
            mostrar_actual_poseedor = True
            if entrega.status == "5":
                mostrar_token = True
            if entrega.status == "2":
                mostrar_pedir_token = True
                siguiente_estado = 3

            if entrega.status == "3":
                siguiente_estado = 5
                mostrar_boton_aceptar = True
                if entrega.user == current_user:
                    conceptos_eliminables = True

        if entrega.get_es_mi_entrega_propietario(current_user):
            mostrar_actual_poseedor = True
            if entrega.status == "2":
                mostrar_pedir_token = True
                siguiente_estado = 4

            if entrega.status == "5":
                mostrar_pedir_token = True
                siguiente_estado = 4

            if entrega.status == "4":
                siguiente_estado = 6
                mostrar_boton_aceptar = True
                if entrega.user == current_user:
                    conceptos_eliminables = True

        contexto["mostrar_actual_poseedor"] = mostrar_actual_poseedor
        contexto["mostrar_boton_aceptar"] = mostrar_boton_aceptar
        contexto["mostrar_pedir_token"] = mostrar_pedir_token
        contexto["mostrar_token"] = mostrar_token
        contexto["siguiente_estado"] = siguiente_estado
        contexto["conceptos_eliminables"] = conceptos_eliminables
        contexto["form_new_concepto"] = new_concepto
        return contexto


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

    def post(self, request, *args, **kwargs):
        form = self.get_form()
        id_ent = self.request.POST.get("id_ent")
        entrega = get_object_or_404(Entrega, id=id_ent)
        conceptos_eliminables = self.request.POST.get("conceptos_eliminables")

        if form.is_valid():
            dia = int(self.request.POST.get("fecha_day"))
            mes = int(self.request.POST.get("fecha_month"))
            ano = int(self.request.POST.get("fecha_year"))
            valor = int(self.request.POST.get("valor"))
            tipo_id = int(self.request.POST.get("tipo"))

            fecha = datetime.datetime(year=ano, month=mes, day=dia)
            tipo = get_object_or_404(ConceptoTipo, id=tipo_id)
            new_concepto = Concepto(fecha=fecha, entrega=entrega, valor=valor, tipo=tipo)
            new_concepto.save()

            return redirect(entrega)

        context = {
            "form_new_concepto": form,
            "object": entrega,
            "conceptos_eliminables": conceptos_eliminables,
        }
        return render(request, "entregas/entrega_detail.html", context)


class ConceptoDeleteView(LoginRequiredMixin, DeleteView):
    def post(self, request, *args, **kwargs):
        if request.user.is_authenticated():
            id_concepto = self.request.POST.get("id_concept")
            concepto = get_object_or_404(Concepto, id=id_concepto)
            entrega = concepto.entrega
            concepto.delete()
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
            entrega.delete()

        return redirect(reverse("entregas:entrega-list"))

        # def post(self, request, *args, **kwargs):
        #     form = ConceptoForm(request.POST or None)
        #     id_ent = request.POST.get("id_ent")
        #     entrega = get_object_or_404(Entrega, id=id_ent)
        #     if request.is_ajax():
        #         if form.is_valid():
        #             id_ent = request.POST.get("id_ent")
        #             dia = int(request.POST.get("fecha_day"))
        #             mes = int(request.POST.get("fecha_month"))
        #             ano = int(request.POST.get("fecha_year"))
        #             valor = int(request.POST.get("valor"))
        #             tipo_id = int(request.POST.get("tipo"))
        #
        #             fecha = datetime.datetime(year=ano, month=mes, day=dia)
        #             tipo = get_object_or_404(ConceptoTipo, id=tipo_id)
        #             new_concepto = Concepto(fecha=fecha, entrega=entrega, valor=valor, tipo=tipo)
        #
        #             locale.setlocale(locale.LC_TIME, "es_ES")
        #             fecha_string = "%s de %s de %s" %(dia,str.capitalize(fecha.strftime("%B")),ano)
        #
        #
        #             context = {
        #                 "is_valid": True,
        #                 "id": new_concepto.id,
        #                 "fecha": fecha_string,
        #                 "tipo": tipo.nombre,
        #                 "valor": valor
        #             }
        #         else:
        #             context = {
        #                 "is_valid": False,
        #                 "errors": form.errors
        #             }
        #         return JsonResponse(context)
        #
        #     context = {
        #         "object": self.get_object()
        #     }
        #     return render(request, entrega.get_absolute_url(), context)
