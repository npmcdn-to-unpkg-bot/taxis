from django.contrib import admin


from .models import Taxi, Propietario, Administrador, Taxista, Portero

# Register your models here.

admin.site.register(Taxi)
admin.site.register(Propietario)
admin.site.register(Administrador)
admin.site.register(Taxista)
admin.site.register(Portero)
