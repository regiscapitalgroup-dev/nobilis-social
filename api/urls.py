from django.urls import path, include
from nsocial.views import (
    ChangePasswordView,
    SetNewPasswordView,
    ForgotMyPassword,
    PasswordResetConfirmView,
    UserProfileView,
    SocialMediaProfileListCreateView,
    SocialMediaProfileRetrieveUpdateDestroyView,
    FullProfileView,
    AdminProfileView,
    UserVideoDestroyView,
    UserVideoListCreateView,
    ExperienceListView,
    RoleListCreateView,
    RoleDetailView
)
from membership.views import AccountOverviewView
from api.views import CityListView, LanguageListView, RelativeListCreateView, RelativeDetailView, RelationshipCatalogListView, SupportAgentListView, SupportAgentDetailView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


urlpatterns = [
    path('users/current/', AccountOverviewView.as_view()),

    path('change-password/<int:pk>/', ChangePasswordView.as_view()),
    path('password-reset/', ForgotMyPassword.as_view(), name='password_reset'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),    
    path('activate-account/', SetNewPasswordView.as_view(), name='activate-account'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cities/', CityListView.as_view(), name='city-list'),
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('full-profile/', FullProfileView.as_view(), name='full-profile'),
    path('admin-profile/', AdminProfileView.as_view(), name='admin-profile'),
    path('social-profiles/', SocialMediaProfileListCreateView.as_view(), name='social-profile-list-create'),
    path('social-profiles/<int:pk>/', SocialMediaProfileRetrieveUpdateDestroyView.as_view(), name='social-profile-detail'),
    path('profile/videos/', UserVideoListCreateView.as_view(), name='video-list-create'),
    path('experiences/', ExperienceListView.as_view(), name='experience-list'),

    # Relationship catalog endpoint (searchable)
    path('relatives/relationships/', RelationshipCatalogListView.as_view(), name='relationship-catalog-list'),

    # Relatives endpoints
    path('relatives/', RelativeListCreateView.as_view(), name='relative-list-create'),
    path('relatives/<int:pk>/', RelativeDetailView.as_view(), name='relative-detail'),

    # Support Agents (read-only) endpoints
    path('support-agents/', SupportAgentListView.as_view(), name='support-agent-list'),
    path('support-agents/<int:pk>/', SupportAgentDetailView.as_view(), name='support-agent-detail'),

    # Notifications REST endpoints
    path('notifications/', include('notification.urls')),
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
]
