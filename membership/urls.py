from django.urls import path
from .views import ListAvailablePlansView, CreateSubscriptionView, StripeWebhookView, CancelSubscriptionView, SubscriptionStatusView

urlpatterns = [
    path('plans/', ListAvailablePlansView.as_view(), name='price-list'),
    path('subscriptions/create/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscriptions/status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('subscriptions/cancel/', CancelSubscriptionView.as_view(), name='cancel-subscription'),
    path('stripe/webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]