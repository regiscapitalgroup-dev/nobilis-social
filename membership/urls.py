from django.urls import path
from membership.views import (ListAvailablePlansView, CreateSubscriptionView, 
                              StripeWebhookView, CancelSubscriptionView, 
                              SubscriptionStatusView, PlanNobilis, AccountOverviewView, PlanPricesView, ShippingAddressView, MembersSubscriptionsOverviewView, MembersListView, InvitationListCreateView, DependentsListView,
                              IntroductionCatalogListCreateView, IntroductionCatalogDetailView,
                              IntroductionStatusListCreateView, IntroductionStatusDetailView,
                              MemberIntroductionListCreateView, MemberIntroductionDetailView,
                              InviteeQualificationCatalogListCreateView, InviteeQualificationCatalogDetailView,
                              MemberReferralListCreateView, MemberReferralDetailView)

urlpatterns = [
    path('stripe/plans/', ListAvailablePlansView.as_view(), name='price-list'),
    path('nobilis/plans/', PlanNobilis.as_view(), name='nobilis-list'),
    path('nobilis/plans/<int:pk>/', PlanPricesView.as_view(), name='plan-price'),
    path('account/overview/', AccountOverviewView.as_view(), name='account-overview'), # <-- Nueva ruta
    path('subscriptions/create/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscriptions/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscriptions/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('subscriptions/members/overview/', MembersSubscriptionsOverviewView.as_view(), name='members-subscriptions-overview'),
    path('subscriptions/members/list/', MembersListView.as_view(), name='members-list'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
    path('shipping-address/', ShippingAddressView.as_view(), name='shipping-address'),
    path('invitations/', InvitationListCreateView.as_view(), name='invitations-list-create'),
    path('dependents/', DependentsListView.as_view(), name='dependents-list'),

    # Introduction Catalog endpoints
    path('introductions/catalog/', IntroductionCatalogListCreateView.as_view(), name='introduction-catalog-list-create'),
    path('introductions/catalog/<int:pk>/', IntroductionCatalogDetailView.as_view(), name='introduction-catalog-detail'),

    # Introduction Status endpoints
    path('introductions/status/', IntroductionStatusListCreateView.as_view(), name='introduction-status-list-create'),
    path('introductions/status/<int:pk>/', IntroductionStatusDetailView.as_view(), name='introduction-status-detail'),

    # Member Introduction endpoints
    path('introductions/', MemberIntroductionListCreateView.as_view(), name='member-introduction-list-create'),
    path('introductions/<int:pk>/', MemberIntroductionDetailView.as_view(), name='member-introduction-detail'),

    # Member Referral catalog endpoints
    path('referrals/catalog/', InviteeQualificationCatalogListCreateView.as_view(), name='invitee-qualification-catalog-list-create'),
    path('referrals/catalog/<int:pk>/', InviteeQualificationCatalogDetailView.as_view(), name='invitee-qualification-catalog-detail'),

    # Member Referral endpoints
    path('referrals/', MemberReferralListCreateView.as_view(), name='member-referral-list-create'),
    path('referrals/<int:pk>/', MemberReferralDetailView.as_view(), name='member-referral-detail'),
]