from django.contrib import admin
from .models import InviteTmpToken

from api.models import CityCatalog

# Register your models here.
admin.site.register(InviteTmpToken)


@admin.register(CityCatalog)
class CityAdmin(admin.ModelAdmin):
    pass