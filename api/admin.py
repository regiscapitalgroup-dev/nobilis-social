from django.contrib import admin
from .models import InviteTmpToken, Relative, RelationshipCatalog, SupportAgent, PartnerType, PartnershipEnquery

from api.models import CityCatalog

# Register your models here.

@admin.register(InviteTmpToken)
class InviteTmpTokenAdmin(admin.ModelAdmin):
    pass


@admin.register(CityCatalog)
class CityAdmin(admin.ModelAdmin):
    pass


@admin.register(Relative)
class RelativeAdmin(admin.ModelAdmin):
    pass


@admin.register(RelationshipCatalog)
class RelationshipCatalogAdmin(admin.ModelAdmin):
    pass


@admin.register(SupportAgent)
class SupportAgentAdmin(admin.ModelAdmin):
    pass


@admin.register(PartnerType)
class PartnerTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(PartnershipEnquery)
class PartnershipEnqueryAdmin(admin.ModelAdmin):
    pass
