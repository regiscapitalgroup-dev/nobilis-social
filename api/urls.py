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
    AdminProfileBasicView,
    AdminProfileConfidentialView,
    UserVideoListCreateView,
    ExperienceListView,
    RoleListCreateView,
    RoleDetailView,
    ProfilePictureUpdateView,
    AdminProfileBiographyView,
    RecognitionUpdateView,
    ExpertiseUpdateView
 )
from membership.views import AccountOverviewView
from api.views import (
    CityListView,
    LanguageListView,
    RelativeListCreateView,
    RelativeDetailView,
    RelationshipCatalogListView,
    SupportAgentListView,
    SupportAgentDetailView,
    IndustryCatalogListView,
    ProfessionalInterestCatalogListView,
    HobbyCatalogListView,
    UpdateProfileIndustriesView,
    UpdateProfileInterestsView,
    UpdateProfileHobbiesView,
    TokenObtainPairWithSubscriptionView,
    ClubCatalogListView,
    RateExpertiseView,
    InviteUserView,
    ContactMessageListCreateView,
    ContactEmailView, PartnerTypeListView
)
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [
    path('users/current/', AccountOverviewView.as_view()),
    path('my-team-invite/', InviteUserView.as_view(), name='invite-user'),

    path('change-password/<int:pk>/', ChangePasswordView.as_view()),
    path('password-reset/', ForgotMyPassword.as_view(), name='password_reset'),
    path('reset-password/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),    
    path('activate-account/', SetNewPasswordView.as_view(), name='activate-account'),

    # path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/', TokenObtainPairWithSubscriptionView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('cities/', CityListView.as_view(), name='city-list'),
    path('languages/', LanguageListView.as_view(), name='language-list'),
    path('users/profile/', UserProfileView.as_view(), name='user-profile'),
    path('full-profile/', FullProfileView.as_view(), name='full-profile'),
    path('admin-profile/', AdminProfileView.as_view(), name='admin-profile'),
    path('admin-profile/basic/', AdminProfileBasicView.as_view(), name='admin-profile-basic'),
    path('admin-profile/confidential/', AdminProfileConfidentialView.as_view(), name='admin-profile-confidential'),
    path('admin-profile/biography/', AdminProfileBiographyView.as_view(), name='admin-profile-biography'),
    path('admin-profile/basic/social-media/', SocialMediaProfileListCreateView.as_view(), name='admin-profile-basic-social-media'),
    path('social-profiles/', SocialMediaProfileListCreateView.as_view(), name='social-profile-list-create'),
    path('social-profiles/<int:pk>/', SocialMediaProfileRetrieveUpdateDestroyView.as_view(), name='social-profile-detail'),
    path('profile/videos/', UserVideoListCreateView.as_view(), name='video-list-create'),
    path('profile/picture/', ProfilePictureUpdateView.as_view(), name='profile-picture'),
    path('profile/recognition/', RecognitionUpdateView.as_view(), name='profile-recognition'),
    path('profile/expertise/', ExpertiseUpdateView.as_view(), name='profile-expertise'),
    path('experiences1/', ExperienceListView.as_view(), name='experience-list'),

    # Relationship catalog endpoint (searchable)
    path('relatives/relationships/', RelationshipCatalogListView.as_view(), name='relationship-catalog-list'),

    # Relatives endpoints
    path('relatives/', RelativeListCreateView.as_view(), name='relative-list-create'),
    path('relatives/<int:pk>/', RelativeDetailView.as_view(), name='relative-detail'),

    # Support Agents (read-only) endpoints
    path('support-agents/', SupportAgentListView.as_view(), name='support-agent-list'),
    path('support-agents/<int:pk>/', SupportAgentDetailView.as_view(), name='support-agent-detail'),

    # Catalog endpoints for industries, professional interests, hobbies, and clubs
    path('catalog/industries/', IndustryCatalogListView.as_view(), name='industry-catalog-list'),
    path('catalog/professional-interests/', ProfessionalInterestCatalogListView.as_view(), name='professional-interest-catalog-list'),
    path('catalog/hobbies/', HobbyCatalogListView.as_view(), name='hobby-catalog-list'),
    path('catalog/clubs/', ClubCatalogListView.as_view(), name='club-catalog-list'),
    path('catalog/rate-expertise/', RateExpertiseView.as_view(), name='rate-expertise'),

    path('profile/industries/', UpdateProfileIndustriesView.as_view(), name='update-profile-industries'),
    path('profile/professional-interests/', UpdateProfileInterestsView.as_view(), name='update-profile-interests'),
    path('profile/hobbies/', UpdateProfileHobbiesView.as_view(), name='update-profile-hobbies'),

    path('notifications/', include('notification.urls')),
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<int:pk>/', RoleDetailView.as_view(), name='role-detail'),
    path('contact/', ContactMessageListCreateView.as_view(), name='contact-list-create'),
    path('contact-email/', ContactEmailView.as_view(), name='contact-email'),
    path('partner-types/', PartnerTypeListView.as_view(), name='partner-type-list'),
]
