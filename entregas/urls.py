from django.conf.urls import url

from .views import EntregaListView,EntregaDetailView, EntregaCreateView, ConceptoCreateView, ConceptoDeleteView,EntregaDeleteView

urlpatterns = [
    url(r'^$', EntregaListView.as_view(), name='entrega-list'),
    url(r'^(?P<pk>\d+)/$', EntregaDetailView.as_view(), name='entrega-detail'),
    url(r'^create/$', EntregaCreateView.as_view(), name='entrega-create'),
    url(r'^concepto/create/$', ConceptoCreateView.as_view(), name='concepto-create'),
    url(r'^concepto/delete/$', ConceptoDeleteView.as_view(), name='concepto-delete'),
    url(r'^delete/$', EntregaDeleteView.as_view(), name='entrega-delete'),
]
