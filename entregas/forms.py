import datetime
from django.db import models
from django.forms import ModelForm, Select, NumberInput
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.admin.widgets import AdminDateWidget
from .models import Entrega, Concepto


class EntregaForm(ModelForm):
    class Meta:
        model = Entrega

        fields = ['fecha','taxi']

        widgets = {
            'fecha': SelectDateWidget(attrs={'class':"form-control"},years=range(datetime.date.today().year-1, datetime.date.today().year+1)),
            'taxi': Select(attrs={'class':"form-control"}),
        }

class ConceptoForm(ModelForm):
    class Meta:
        model = Concepto
        fields = ['fecha','tipo', 'valor']

        widgets = {
            'fecha': SelectDateWidget(attrs={'class':"form-control"},years=range(datetime.date.today().year-1, datetime.date.today().year+1)),
            'tipo': Select(attrs={'class': "form-control"}),
            'valor': NumberInput(attrs={'class': "form-control"}),
        }
