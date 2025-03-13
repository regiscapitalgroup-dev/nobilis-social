from django.urls import path
from .views import waitinglistView, waitinglistDetailView


urlpatterns = [ 
    path('waitinglist/', waitinglistView),
    path('waitinglist/<int:pk>/', waitinglistDetailView),
]
