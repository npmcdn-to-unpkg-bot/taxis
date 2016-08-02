from django.shortcuts import render

# Create your views here.
from django.views.generic import ListView

from taxis.models import Taxi


class TaxiListView(ListView):
    model = Taxi

    def get_queryset(self):
        qs = Taxi.objects.get_mis_taxis(self.request.user)
        return qs