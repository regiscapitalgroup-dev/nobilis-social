from django.urls import path
from .views import WaitingListAPIView, WaitingListDetailAPIView
from nsocial.views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [ 
    path('waitinglist/', WaitingListAPIView.as_view()),
    path('waitinglist/<int:pk>/', WaitingListDetailAPIView.as_view()),

    path('register/', RegisterView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
]
