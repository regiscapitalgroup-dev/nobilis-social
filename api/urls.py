from django.urls import path
from .views import WaitingListAPIView, WaitingListDetailAPIView
from nsocial.views import RegisterView


urlpatterns = [ 
    path('waitinglist/', WaitingListAPIView.as_view()),
    path('waitinglist/<int:pk>/', WaitingListDetailAPIView.as_view()),

    path('register/', RegisterView.as_view())
]
