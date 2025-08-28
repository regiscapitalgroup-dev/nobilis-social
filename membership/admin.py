from django.contrib import admin
from membership.models import Plan, ShippingAddress  # , Subscription

# Register your models here.
admin.site.register(Plan)
#admin.site.register(Subscription)
admin.site.register(ShippingAddress)

