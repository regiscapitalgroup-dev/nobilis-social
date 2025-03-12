from django.urls import path
from waitinglist.views import waiting_list

urlpatterns = [ 
    path('', waiting_list, name="waitinglist")
]