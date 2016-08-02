import datetime
from django.db import models
from django.forms import ModelForm
from django.forms.extras.widgets import SelectDateWidget
from django.contrib.admin.widgets import AdminDateWidget
from .models import Entrega, Concepto


class EntregaForm(ModelForm):
    class Meta:
        model = Entrega
        fields = ['fecha','taxi']

        widgets = {
             'fecha': SelectDateWidget(years=range(datetime.date.today().year-1, datetime.date.today().year+1)),
        }

class ConceptoForm(ModelForm):
    class Meta:
        model = Concepto
        fields = ['fecha','tipo', 'valor']

        widgets = {
             'fecha': SelectDateWidget(years=range(datetime.date.today().year-1, datetime.date.today().year+1)),
        }
