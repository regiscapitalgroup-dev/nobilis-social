from django.urls import path
from api.views import WaitingListView, WaitingListDetailView, CategoryView, MotivationView, CategoryDetailView, MotivationDetailView
from nsocial.views import RegisterView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [ 
    path('waitinglist/', WaitingListView.as_view()),
    path('waitinglist/<int:pk>/', WaitingListDetailView.as_view()),
    path('category/', CategoryView.as_view()),
    path('category/<int:pk>/', CategoryDetailView.as_view()),
    path('motivation/', MotivationView.as_view()),
    path('motivation/<int:pk>', MotivationDetailView.as_view()),

    path('register/', RegisterView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
]
