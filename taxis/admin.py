from django.contrib import admin


from .models import Taxi, Propietario, Administrador, Taxista

# Register your models here.

admin.site.register(Taxi)
admin.site.register(Propietario)
admin.site.register(Administrador)
admin.site.register(Taxista)
