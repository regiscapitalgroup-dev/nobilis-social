from django.contrib import admin
from .models import WaitingList, RejectionReason

# Register your models here.
admin.site.register(WaitingList)
admin.site.register(RejectionReason)
