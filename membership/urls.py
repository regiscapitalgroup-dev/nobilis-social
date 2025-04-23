from django.urls import path
from membership.views import (ListAvailablePlansView, CreateSubscriptionView, 
                              StripeWebhookView, CancelSubscriptionView, 
                              SubscriptionStatusView, PlanNobilis, AccountOverviewView)

urlpatterns = [
    path('stripe/plans/', ListAvailablePlansView.as_view(), name='price-list'),
    path('nobilis/plans/', PlanNobilis.as_view(), name='nobilis-list'),
    path('account/overview/', AccountOverviewView.as_view(), name='account-overview'), # <-- Nueva ruta
    path('subscriptions/create/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscriptions/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscriptions/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]