from django.contrib import admin

from .models import Entrega, ConceptoTipo, Concepto


# Define an inline admin descriptor for Employee model
# which acts a bit like a singleton
class Concepto_Inline(admin.StackedInline):
    model = Concepto
    can_delete = False
    verbose_name_plural = 'concepto'


# Register your models here.
# Define a new User admin
class EntregarAdmin(admin.ModelAdmin):
    inlines = [
        Concepto_Inline,
    ]


# Re-register UserAdmin
admin.site.register(Entrega, EntregarAdmin)
admin.site.register(ConceptoTipo)
