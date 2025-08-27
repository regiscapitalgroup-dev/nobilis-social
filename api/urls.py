from django.urls import path, include
from waitinglist.views import WaitingListDetailView, WaitingListInviteView, WaitingListView, UserExistsView
from nsocial.views import (ChangePasswordView, SetNewPasswordView, ForgotMyPassword, PasswordResetConfirmView,
                           UserProfileView, SocialMediaProfileListCreateView, SocialMediaProfileRetrieveUpdateDestroyView)
from membership.views import AccountOverviewView
from api.views import CityListView, LanguageListView
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
    path('password-reset/', ForgotMyPassword.as_view(), name='password_reset'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),    
    path('activate-account/', SetNewPasswordView.as_view(), name='activate-account'),

    path('members/', include('membership.urls')),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cities/', CityListView.as_view(), name='city-list'),
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('social-profiles/', SocialMediaProfileListCreateView.as_view(), name='social-profile-list-create'),
    path('social-profiles/<int:pk>/', SocialMediaProfileRetrieveUpdateDestroyView.as_view(), name='social-profile-detail'),
]
