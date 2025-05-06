from django.urls import path, include
from waitinglist.views import WaitingListDetailView, WaitingListInviteView, WaitingListView, UserExistsView
from nsocial.views import ChangePasswordView, SetNewPasswordView
#from membership.views import MembershipPlanView, MembershipPlanDetail, SuscriptionView, SuscriptionDetailView
from nsocial.views import RegisterView, CurrentUserView
from membership.views import AccountOverviewView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [ 
    path('waitinglist/', WaitingListView.as_view(), name='waitinglist'),
    path('waitinglist/<int:pk>/', WaitingListDetailView.as_view()),
    path('waitinglist/invite/<int:pk>/', WaitingListInviteView.as_view()),
    path('waitinglist/exists/', UserExistsView.as_view()),
    path('users/current/', AccountOverviewView.as_view()),

    path('change-password/<int:pk>/', ChangePasswordView.as_view()),
    path('activate-account/', SetNewPasswordView.as_view(), name='activate-account'),

    path('members/', include('membership.urls')),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),    
]
