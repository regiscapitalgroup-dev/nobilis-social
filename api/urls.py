from django.urls import path
from api.views import WaitingListDetailView, WaitingListView
from nsocial.views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [ 
    path('waitinglist/', WaitingListView.as_view()),
    path('waitinglist/<int:pk>/', WaitingListDetailView.as_view()),

    path('register/', RegisterView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
]
