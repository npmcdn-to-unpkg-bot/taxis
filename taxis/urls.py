from django.conf.urls import url

from .views import TaxiListView

urlpatterns = [
    url(r'^$', TaxiListView.as_view(), name='taxi-list'),
    ]

