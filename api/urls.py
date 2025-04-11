from django.urls import path
from waitinglist.views import WaitingListDetailView, WaitingListInviteView, WaitingListView
from nsocial.views import ChangePasswordView, SetNewPasswordView
from membership.views import MembershipPlanView, MembershipPlanDetail
from nsocial.views import RegisterView, CurrentUserView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [ 
    path('waitinglist/', WaitingListView.as_view(), name='waitinglist'),
    path('waitinglist/<int:pk>/', WaitingListDetailView.as_view()),
    path('waitinglist/invite/<int:pk>/', WaitingListInviteView.as_view()),
    path('users/current/', CurrentUserView.as_view()),

    path('change-password/<int:pk>/', ChangePasswordView.as_view()),
    path('activate-account/', SetNewPasswordView.as_view(), name='activate-account'),

    path('membership/', MembershipPlanView.as_view(), name='membership'),
    path('membership/<int:pk>/', MembershipPlanDetail.as_view(), name='membership-detail'),
    
    # path('register/', RegisterView.as_view()),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
]
