from django.contrib import admin
from .models import (
    InviteTmpToken,
    Relative,
    RelationshipCatalog,
    SupportAgent,
    PartnerType,
    PartnershipEnquery,
    IndustryCatalog
)
from api.models import CityCatalog


@admin.register(InviteTmpToken)
class InviteTmpTokenAdmin(admin.ModelAdmin):
    pass


@admin.register(CityCatalog)
class CityAdmin(admin.ModelAdmin):
    list_display = ('name', 'subcountry', 'country')
    search_fields = ('name', 'subcountry', 'country')


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


@admin.register(IndustryCatalog)
class IndustryCatalogAdmin(admin.ModelAdmin):
    pass
