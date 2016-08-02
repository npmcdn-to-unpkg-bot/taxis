import datetime

from django.core.urlresolvers import reverse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import ListView, DetailView, DeleteView
from django.views.generic.edit import CreateView

# Create your views here.


from .forms import EntregaForm, ConceptoForm

from .models import Entrega, Concepto, ConceptoTipo
from taxis.models import Taxi


class EntregaListView(ListView):
    model = Entrega

    def get_queryset(self):
        qs = Entrega.objects.get_mis_entregas(self.request.user)
        return qs


class EntregaDetailView(DetailView):
    model = Entrega

    def get_context_data(self, **kwargs):
        new_concepto = ConceptoForm
        contexto = super().get_context_data(**kwargs)

        entrega = contexto["object"]
        taxi = entrega.taxi

        conceptos_eliminables=False

        if taxi.es_conductor(self.request.user) and (entrega.status=="1" or entrega.status=="5"):
            conceptos_eliminables=True

        if taxi.es_administrador(self.request.user) and entrega.status == "2":
            conceptos_eliminables = True

        if taxi.es_propietario(self.request.user) and int(entrega.status) > 1 :
            conceptos_eliminables = True

        contexto["conceptos_eliminables"] = conceptos_eliminables
        contexto["form_new_concepto"] = new_concepto
        return contexto


class EntregaCreateView(CreateView):
    model = Entrega
    form_class = EntregaForm

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        user = self.request.user
        qst = Taxi.objects.get_mis_taxis(user)
        form.fields["taxi"].queryset = qst
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
            entrega = Entrega(actual_poseedor=user, taxi=taxi, user=user, fecha=fecha)
            entrega.save()
            return redirect(entrega.get_absolute_url())
        return super(EntregaCreateView, self).post(request, *args, **kwargs)


class ConceptoCreateView(CreateView):
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
            "conceptos_eliminables" : conceptos_eliminables,
        }
        return render(request, "entregas/entrega_detail.html", context)


class ConceptoDeleteView(DeleteView):
    def post(self, request, *args, **kwargs):
        id_concepto = self.request.POST.get("id_concept")
        concepto = get_object_or_404(Concepto, id=id_concepto)
        entrega = concepto.entrega
        concepto.delete()
        return redirect(entrega)

class EntregaDeleteView(DeleteView):
    def post(self, request, *args, **kwargs):
        id_ent = self.request.POST.get("id_ent")
        entrega = get_object_or_404(Entrega, id=id_ent)
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
