from django.urls import path
from .views import PlanListView, CreateSubscriptionView, stripe_webhook_view, SubscriptionDetailView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plan-list'),
    path('subscriptions/create/', CreateSubscriptionView.as_view(), name='create-subscription'),
    path('subscriptions/me/', SubscriptionDetailView.as_view(), name='user-subscription'),
    path('stripe/webhook/', stripe_webhook_view, name='stripe-webhook'),
]