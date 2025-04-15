from rest_framework import generics, permissions, status
from rest_framework.response import Response
from .models import Plan, Subscription
from .serializers import PlanSerializer, CreateSubscriptionSerializer, SubscriptionSerializer
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import stripe
import json

stripe.api_key = settings.STRIPE_SECRET_KEY

class PlanListView(generics.ListAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny] # O la que necesites

class CreateSubscriptionView(generics.CreateAPIView):
    serializer_class = CreateSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        plan_id = serializer.validated_data['plan_id']
        payment_method_id = serializer.validated_data['payment_method_id']
        user = self.request.user
        plan = get_object_or_404(Plan, id=plan_id)

        try:
            customer = stripe.Customer.retrieve(user.stripe_customer_id) if hasattr(user, 'stripe_customer_id') and user.stripe_customer_id else stripe.Customer.create(email=user.email)
            user.stripe_customer_id = customer.id
            user.save()

            stripe.PaymentMethod.attach(payment_method_id, customer=customer.id)
            stripe.Customer.update(customer.id, invoice_settings={'default_payment_method': payment_method_id})

            stripe_subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{'plan': plan.stripe_plan_id}],
            )

            Subscription.objects.create(
                user=user,
                plan=plan,
                stripe_subscription_id=stripe_subscription.id,
                status=stripe_subscription.status,
                current_period_start=stripe_subscription.current_period_start,
                current_period_end=stripe_subscription.current_period_end,
            )
            return Response({'message': 'Subscription created successfully.'}, status=status.HTTP_201_CREATED)

        except stripe.error.StripeError as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class SubscriptionDetailView(generics.RetrieveAPIView):
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
            subscriptions = Subscription.objects.filter(user=request.user)
            if subscriptions.exists():
                serializer = self.serializer_class(subscriptions.first())
                return Response(serializer.data)
            else:
                return Response({'detail': 'No subscription found for this user.'}, status=status.HTTP_404_NOT_FOUND)
    

@csrf_exempt
def stripe_webhook_view(request):
    payload = request.body
    sig_header = request.META['HTTP_STRIPE_SIGNATURE']
    event = None

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except ValueError as e:
        # Invalid payload
        return HttpResponse(status=400)
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        return HttpResponse(status=400)

    if event['type'] == 'customer.subscription.updated' or event['type'] == 'customer.subscription.deleted':
        stripe_subscription = event['data']['object']
        try:
            subscription = Subscription.objects.get(stripe_subscription_id=stripe_subscription['id'])
            subscription.status = stripe_subscription['status']
            subscription.current_period_start = stripe_subscription['current_period_start']
            subscription.current_period_end = stripe_subscription['current_period_end']
            subscription.save()
            print(f"Subscription {subscription.stripe_subscription_id} updated to {subscription.status}")
        except Subscription.DoesNotExist:
            print(f"Subscription not found: {stripe_subscription['id']}")
        except Exception as e:
            print(f"Error updating subscription {stripe_subscription['id']}: {e}")

    elif event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                print(f"Payment succeeded for subscription: {subscription.stripe_subscription_id}")
                # Aquí puedes realizar acciones adicionales, como actualizar el acceso del usuario
            except Subscription.DoesNotExist:
                print(f"Subscription not found for successful payment: {subscription_id}")

    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        subscription_id = invoice.get('subscription')
        if subscription_id:
            try:
                subscription = Subscription.objects.get(stripe_subscription_id=subscription_id)
                subscription.status = 'past_due' # O el estado que consideres apropiado
                subscription.save()
                print(f"Payment failed for subscription: {subscription.stripe_subscription_id}")
                # Aquí puedes notificar al usuario sobre el fallo de pago
            except Subscription.DoesNotExist:
                print(f"Subscription not found for failed payment: {subscription_id}")

    # Otros eventos que quieras manejar

    return HttpResponse(status=200)
