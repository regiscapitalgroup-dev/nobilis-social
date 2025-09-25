from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from membership.models import Plan, MembershipSubscription, IntroductionCatalog, IntroductionStatus, MemberIntroduction, InviteeQualificationCatalog, MemberReferral
from django.utils.decorators import method_decorator
from membership.serializers import (PriceSerializer, SubscriptionCreateSerializer,
                                    SubscriptionStatusSerializer, PlanNobilisSerializer, PlanNobilisPriceSerializer,
                                    ShippingAddressSerializer, MembershipSubscriptionSerializer, UserInvitationSerializer, DependentUserSerializer,
                                    IntroductionCatalogSerializer, IntroductionStatusSerializer, MemberIntroductionSerializer,
                                    InviteeQualificationCatalogSerializer, MemberReferralSerializer)
from nsocial.models import UserProfile
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import logging
import stripe
from django.utils import timezone
import datetime as dt
from django.conf import settings
from django.db import models
from django.db.models import Min
from django.contrib.auth import get_user_model
from decimal import Decimal


stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)


class ListAvailablePlansView(APIView):
    """
    Lista los planes (Precios activos de Stripe) disponibles para suscripción.
    """
    permission_classes = [permissions.AllowAny] # Generalmente, listar planes es público

    def get(self, request, *args, **kwargs):
        try:
            # Llama a la API de Stripe para obtener precios activos
            # 'expand' incluye el objeto completo del Producto asociado a cada Precio
            prices = stripe.Price.list(
                active=True,
                type='recurring', # Asegura que solo obtienes precios de suscripción
                expand=['data.product'] # ¡Importante para obtener info del producto!
                # Puedes añadir paginación si tienes muchos precios: limit=10, etc.
            )

            # Usa el serializer para formatear los datos de Stripe
            # prices.data contiene la lista de objetos Price de Stripe
            serializer = PriceSerializer(prices.data, many=True)

            return Response(serializer.data, status=status.HTTP_200_OK)

        except stripe.error.StripeError as e:
            # Manejo de errores de Stripe
            return Response(
                {"error": f"Error al obtener planes de Stripe: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR # O un código más específico si aplica
            )
        except Exception as e:
            # Manejo de otros errores inesperados
            # Considera loggear el error
            return Response(
                {"error": "Ocurrió un error inesperado."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreateSubscriptionView(APIView):
    """
    Maneja la creación del cliente Stripe (si es necesario),
    la configuración del método de pago y la creación de la suscripción
    en una sola llamada.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        # Usa el serializer original que espera ambos IDs
        serializer = SubscriptionCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        payment_method_id = serializer.validated_data['payment_method_id']
        price_id = serializer.validated_data['price_id']
        user = request.user

        try:
            # 0. Verificar que el método de pago existe en Stripe
            try:
                payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
            except stripe.error.InvalidRequestError as e:
                logger.error(f"Error: Método de pago no encontrado: {payment_method_id}. Error: {e}")
                return Response(
                    {"error": f"El método de pago proporcionado no existe o no es válido: {str(e)}", "code": e.code},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 1. Obtener el perfil del usuario
            profile = get_object_or_404(UserProfile, user=user)
            customer_id = profile.stripe_customer_id
            customer_created_now = False # Flag

            # 2. Crear Cliente en Stripe SI NO EXISTE (intentando pasar PM)
            if not customer_id:
                try:
                    # Intenta crear cliente + adjuntar PM + establecer default
                    customer = stripe.Customer.create(
                        email=user.email,
                        name=f"{user.first_name} {user.last_name}".strip(),
                        metadata={'django_user_id': user.id},
                        payment_method=payment_method_id, # Intenta adjuntar
                        invoice_settings={             # Intenta establecer default
                            'default_payment_method': payment_method_id,
                        }
                    )
                    customer_id = customer.id
                    profile.stripe_customer_id = customer_id
                    customer_created_now = True
                except stripe.error.StripeError as e:
                    logger.error(f"Error creando cliente Stripe para user {user.id}: {e}", exc_info=True)
                    return Response({"error": f"Error creando perfil de pago: {str(e)}", "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

            # 3. Adjuntar y Establecer PM como Default *SI EL CLIENTE YA EXISTÍA*
            #    (Si fue recién creado, ya se intentó en el paso anterior)
            if not customer_created_now:
                try:
                    stripe.PaymentMethod.attach(payment_method_id, customer=customer_id)
                    stripe.Customer.modify(
                        customer_id,
                        invoice_settings={'default_payment_method': payment_method_id},
                    )
                except stripe.error.StripeError as e:
                    logger.error(f"Error adjuntando/modificando PM {payment_method_id} para customer {customer_id}: {e}", exc_info=True)
                    return Response({"error": f"Error al configurar el método de pago: {str(e)}", "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

            # 4. (Opcional) Guardar/Actualizar detalles del PM en el Perfil local
            try:
                pm_details = stripe.PaymentMethod.retrieve(payment_method_id)
                if pm_details.type == 'card':
                    profile.stripe_payment_method_id = pm_details.id
                    profile.card_brand = pm_details.card.brand
                    profile.card_last4 = pm_details.card.last4
                else:
                     profile.stripe_payment_method_id = pm_details.id
                     profile.card_brand = pm_details.type
                     profile.card_last4 = None
            except stripe.error.StripeError as pm_error:
                 logger.warning(f"No se pudieron guardar detalles del método de pago {payment_method_id} para customer {customer_id}: {pm_error}")
            finally:
                 # Guardar perfil (con customer_id si era nuevo, y detalles PM)
                 # Es importante guardar aquí por si el customer_id se asignó arriba
                 profile.save()

            # 5. Crear la Suscripción en Stripe
            try:
                subscription = stripe.Subscription.create(
                    customer=customer_id,
                    items=[{'price': price_id}],
                    # expand=['latest_invoice.payment_intent'],
                    expand=['latest_invoice']
                )
                profile.stripe_subscription_id = subscription.id
                profile.subscription_status = subscription.status

                # Determinar plan local a partir del price de Stripe
                price_id = None
                try:
                    if hasattr(subscription, 'items') and subscription.items and subscription.items.data:
                        price_id = subscription.items.data[0].price.id
                except Exception:
                    price_id = None

                plan = Plan.objects.filter(stripe_plan_id=price_id).first() if price_id else None
                # Crear/actualizar fila de MembershipSubscription
                from django.utils import timezone
                import datetime as dt

                current_period_end = None
                try:
                    ts = getattr(subscription, 'current_period_end', None)
                    current_period_end = dt.datetime.fromtimestamp(ts, tz=dt.timezone.utc) if ts else None
                except Exception:
                    pass

                sub_obj, _ = MembershipSubscription.objects.update_or_create(
                    stripe_subscription_id=subscription.id,
                    defaults={
                        'user_profile': profile,
                        'plan': plan,
                        'status': subscription.status,
                        'cancel_at_period_end': getattr(subscription, 'cancel_at_period_end', False),
                        'current_period_end': current_period_end,
                        'is_active': subscription.status in ['active', 'trialing'] and not getattr(subscription,
                                                                                                   'canceled_at', None),
                    }
                )

                # Puntero de conveniencia en el perfil
                profile.current_subscription = sub_obj
                profile.save()

                # 6. Manejar la respuesta de la suscripción
                response_data = {
                    'subscription_id': subscription.id,
                    'status': subscription.status,
                }
                #if subscription.status == 'incomplete' and subscription.latest_invoice.payment_intent.status == 'requires_action':
                #     response_data['client_secret'] = subscription.latest_invoice.payment_intent.client_secret

                # Si expandiste solo 'latest_invoice':
                if hasattr(subscription, 'latest_invoice') and subscription.latest_invoice and hasattr(subscription.latest_invoice, 'payment_intent') and subscription.latest_invoice.payment_intent:
                     # Solo intenta acceder si la estructura existe
                     payment_intent_status = getattr(stripe.PaymentIntent.retrieve(subscription.latest_invoice.payment_intent), 'status', None) # Recuperar explícitamente si es necesario
                     if subscription.status == 'incomplete' and payment_intent_status == 'requires_action':
                           # Necesitas el client_secret del PaymentIntent, no está directamente aquí
                           # Recupera el PI completo:
                           try:
                               pi = stripe.PaymentIntent.retrieve(subscription.latest_invoice.payment_intent)
                               response_data['client_secret'] = pi.client_secret
                           except stripe.error.StripeError as pi_error:
                                logger.error(f"Error recuperando PaymentIntent {subscription.latest_invoice.payment_intent} para SCA: {pi_error}")

                # Actualizar perfil local con datos de la suscripción creada
                profile.stripe_subscription_id = subscription.id
                profile.subscription_status = subscription.status
                # profile.update_subscription_details(subscription) # Podrías usar un helper
                profile.save() # Guardar los últimos cambios

                return Response(response_data, status=status.HTTP_201_CREATED)

            except stripe.error.StripeError as e:
                logger.error(f"Error creando suscripción para customer {customer_id}: {e}", exc_info=True)
                return Response({"error": f"No se pudo crear la suscripción: {str(e)}", "code": e.code}, status=status.HTTP_400_BAD_REQUEST)

        except UserProfile.DoesNotExist:
             logger.error(f"UserProfile no encontrado para usuario autenticado {user.id}")
             return Response({"error": "Perfil de usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado en CreateSubscriptionView para user {user.id}: {e}", exc_info=True)
            return Response({"error": "Ocurrió un error inesperado."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
class CancelSubscriptionView(APIView):
    """
    Marca la suscripción activa o de prueba del usuario para cancelación
    al final del periodo de facturación actual.
    """
    permission_classes = [permissions.IsAuthenticated] # Requiere autenticación

    def post(self, request, *args, **kwargs): # Usamos POST para una acción de cambio de estado
        user = request.user
        now = timezone.now() # Fecha actual (viernes, 18 de abril de 2025 17:38:33 MST)

        try:
            # 1. Obtener perfil y customer_id
            profile = get_object_or_404(UserProfile, user=user)
            customer_id = profile.stripe_customer_id

            if not customer_id:
                return Response({"error": "Usuario no encontrado en Stripe."}, status=status.HTTP_404_NOT_FOUND)

            # 2. Encontrar la suscripción activa o en prueba del usuario
            # Es más robusto buscar por ambas por si acaso.
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='all', # Traemos todas las activas/en prueba/pasadas para estar seguros
                expand=['data.plan.product'] # Para poder devolver info completa si es necesario
            )

            active_subscription = None
            for sub in subscriptions.data:
                # Buscamos la primera activa o en prueba que NO esté ya cancelada o incompleta
                if sub.status in ['active', 'trialing'] and not sub.cancel_at_period_end:
                    active_subscription = sub
                    break # Encontramos la candidata a cancelar

            if not active_subscription:
                 # Podríamos verificar si ya hay una marcada para cancelar
                 already_canceling = False
                 cancel_date = None
                 for sub in subscriptions.data:
                      if sub.status in ['active', 'trialing'] and sub.cancel_at_period_end:
                           already_canceling = True
                           cancel_date = dt.datetime.fromtimestamp(sub.current_period_end, tz=dt.timezone.utc)
                           break
                 if already_canceling:
                      return Response({
                          "message": "Tu suscripción ya está programada para cancelarse.",
                          "cancel_at": cancel_date.isoformat()
                          }, status=status.HTTP_400_BAD_REQUEST)
                 else:
                      # No hay ninguna activa/en prueba o ya están inactivas/canceladas.
                      return Response({"error": "No se encontró una suscripción activa para cancelar."}, status=status.HTTP_404_NOT_FOUND)


            # 3. Marcar la suscripción para cancelación al final del periodo
            try:
                subscription_id_to_cancel = active_subscription.id
                canceled_subscription = stripe.Subscription.modify(
                    subscription_id_to_cancel,
                    cancel_at_period_end=True
                )

                try:
                    sub_id = subscription_id_to_cancel
                    MembershipSubscription.objects.filter(stripe_subscription_id=sub_id).update(
                        cancel_at_period_end=True
                    )
                except Exception:
                    pass

                # 4. (Opcional) Actualizar estado local via Webhooks es MEJOR,
                #    pero podríamos actualizar algo aquí si es crítico para la UI inmediata.
                #    Ej: profile.subscription_status = 'canceling' (si tienes ese campo)
                #    profile.save()

                # 5. Devolver respuesta exitosa (opcionalmente con datos actualizados)
                serializer = SubscriptionStatusSerializer(canceled_subscription) # Usamos el serializer para formatear

                return Response({
                    "message": "Tu suscripción se cancelará al final del periodo actual.",
                    "subscription": serializer.data # Devuelve el estado actualizado
                    }, status=status.HTTP_200_OK)

            except stripe.error.StripeError as e:
                # Error al intentar modificar la suscripción en Stripe
                return Response(
                    {"error": f"Error al cancelar la suscripción en Stripe: {str(e)}", "code": e.code},
                    status=status.HTTP_400_BAD_REQUEST
                )

        except UserProfile.DoesNotExist:
             return Response({"error": "Perfil de usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # Loggear el error e.g., logging.error("Error inesperado en cancelación: %s", e)
            return Response(
                {"error": "Ocurrió un error inesperado procesando la cancelación."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        

class SubscriptionStatusView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            profile = get_object_or_404(UserProfile, user=user)
            subscription_id = profile.stripe_subscription_id

            if not subscription_id:
                return Response({"success": False, "message": "No subscription record found."}, status=status.HTTP_200_OK) # O 404 si prefieres

            try:
                stripe_subscription = stripe.Subscription.retrieve(
                    subscription_id,
                    expand=[
                        'plan.product',
                        'default_payment_method'
                        ]
                )

                try:
                    local_period_end_ts = int(profile.subscription_current_period_end.timestamp()) if profile.subscription_current_period_end else None

                    stripe_period_end_ts = getattr(stripe_subscription, 'current_period_end', None)
                    stripe_status = getattr(stripe_subscription, 'status', None)
                    stripe_cancel_at_period_end = getattr(stripe_subscription, 'cancel_at_period_end', False) # Default a False

                    if (profile.subscription_status != stripe_status or
                        local_period_end_ts != stripe_period_end_ts or
                        profile.cancel_at_period_end != stripe_cancel_at_period_end):
                           logger.warning(f"Discrepancia detectada para sub {subscription_id} (User {user.id}). Actualizando perfil local desde Stripe.")
                           profile.update_subscription_details(stripe_subscription)

                except Exception as comparison_error:
                     # Loguear si la comparación o actualización local falla, pero no detener el flujo principal
                     logger.error(f"Error durante la comparación/actualización local para sub {subscription_id}: {comparison_error}", exc_info=True)

                # 4. Serializar y devolver los datos FRESCOS de Stripe
                serializer = SubscriptionStatusSerializer(stripe_subscription)
                return Response(serializer.data, status=status.HTTP_200_OK)

            except stripe.error.InvalidRequestError as e:
                # El ID de suscripción local es inválido o fue eliminado en Stripe
                logger.warning(f"Stripe sub retrieve falló para ID local {subscription_id} (User {user.id}): {e}. Limpiando datos locales.")
                profile.clear_subscription_details() # Limpiar datos locales incorrectos
                return Response({"status": "inactive", "message": "La suscripción no se encontró en el sistema de facturación."}, status=status.HTTP_404_NOT_FOUND)
            except stripe.error.StripeError as e:
                # Otro error de API de Stripe (ej: red, autenticación)
                local = None
                try:
                    if subscription_id:
                        local = MembershipSubscription.objects.filter(stripe_subscription_id=subscription_id).first()
                except Exception:
                    local = None

                if local:
                    from membership.serializers import MembershipSubscriptionSerializer
                    return Response({'source': 'local', 'subscription': MembershipSubscriptionSerializer(local).data},
                                    status=status.HTTP_200_OK)
                logger.error(f"Error de API Stripe recuperando sub {subscription_id} (User {user.id}): {e}", exc_info=True)
                # Podríamos devolver datos locales como fallback, pero es mejor indicar el error
                return Response({"error": f"Error al contactar el sistema de facturación: {str(e)}"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        except UserProfile.DoesNotExist:
             logger.error(f"UserProfile no encontrado para usuario autenticado {user.id}")
             return Response({"error": "Perfil de usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error inesperado en SubscriptionStatusView para user {user.id}: {e}", exc_info=True)
            return Response({"error": "Ocurrió un error inesperado."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Exime de la verificación CSRF ya que Stripe no enviará un token CSRF
@method_decorator(csrf_exempt, name='dispatch')
class StripeWebhookView(APIView):
    """
    Escucha los eventos enviados por Stripe.
    """
    permission_classes = [permissions.AllowAny] # Debe ser accesible públicamente

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.headers.get('Stripe-Signature')
        endpoint_secret = settings.STRIPE_WEBHOOK_SECRET
        event = None

        # 1. Verificar la firma del Webhook (¡SEGURIDAD!)
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, endpoint_secret
            )
        except ValueError as e:
            # Payload inválido
            logger.warning("Webhook payload inválido: %s", e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError as e:
            # Firma inválida
            logger.warning("Webhook firma inválida: %s", e)
            return Response(status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
             # Otro error inesperado durante la construcción del evento
             logger.error("Error inesperado construyendo evento webhook: %s", e, exc_info=True)
             return Response(status=status.HTTP_400_BAD_REQUEST)

        # 2. Manejar el evento específico
        event_type = event['type']
        data_object = event['data']['object'] # El objeto de Stripe (Invoice, Subscription, etc.)

        if event_type in ['customer.subscription.created', 'customer.subscription.updated',
                          'customer.subscription.deleted']:
            sub = data_object  # Objeto Subscription de Stripe

            # Ubicar el perfil: preferiblemente por `customer` si lo guardas
            profile = None
            try:
                customer_id = sub.get('customer')
                if customer_id:
                    profile = UserProfile.objects.filter(stripe_customer_id=customer_id).first()
                if not profile:
                    profile = UserProfile.objects.filter(stripe_subscription_id=sub.get('id')).first()
            except Exception:
                profile = None

            # Resolver plan a partir del price del primer item
            price_id = None
            try:
                items = sub.get('items', {}).get('data', [])
                if items:
                    price_id = items[0].get('price', {}).get('id')
            except Exception:
                price_id = None

            plan = Plan.objects.filter(stripe_plan_id=price_id).first() if price_id else None

            # Campos comunes
            status_value = sub.get('status') or ''
            cancel_flag = sub.get('cancel_at_period_end') or False
            cpe = sub.get('current_period_end')
            current_period_end = dt.datetime.fromtimestamp(cpe, tz=dt.timezone.utc) if cpe else None
            is_active = status_value in ['active', 'trialing'] and not sub.get('canceled_at')

            # Upsert de la fila local
            sub_obj, _ = MembershipSubscription.objects.update_or_create(
                stripe_subscription_id=sub.get('id'),
                defaults={
                    'user_profile': profile,
                    'plan': plan,
                    'status': status_value,
                    'cancel_at_period_end': cancel_flag,
                    'current_period_end': current_period_end,
                    'is_active': is_active,
                }
            )

            # Refrescar caché del perfil si lo encontramos
            if profile:
                try:
                    profile.stripe_subscription_id = sub.get('id')
                    profile.subscription_status = status_value
                    profile.subscription_current_period_end = current_period_end
                    profile.cancel_at_period_end = cancel_flag
                    profile.current_subscription = sub_obj
                    profile.save()
                except Exception:
                    pass

            return Response({'received': True}, status=status.HTTP_200_OK)



        logger.info(f"Webhook recibido: {event_type}, Event ID: {event.id}")

        # --- Manejadores de Eventos ---

        if event_type == 'invoice.payment_succeeded':
            # Cliente pagó la factura (inicio de suscripción, renovación)
            try:
                invoice = data_object
                customer_id = invoice.customer
                subscription_id = invoice.subscription # Puede ser null si no es de suscripción

                if subscription_id: # Solo actuar si es una factura de suscripción
                    profile = UserProfile.objects.get(stripe_customer_id=customer_id)

                    # Recuperar la suscripción para obtener el estado y fechas actualizadas
                    stripe_sub = stripe.Subscription.retrieve(subscription_id)
                    profile.update_subscription_details(stripe_sub)

                    logger.info(f"Pago exitoso procesado para Customer {customer_id}, Sub {subscription_id}. Perfil actualizado.")
                    # Aquí podrías enviar un email de confirmación de pago/renovación
                    # usando una tarea asíncrona (ej: Celery)
                    # send_renewal_confirmation_email.delay(profile.user.id)

            except UserProfile.DoesNotExist:
                logger.error(f"Webhook {event_type}: UserProfile no encontrado para customer {customer_id}")
            except stripe.error.StripeError as e:
                 logger.error(f"Webhook {event_type}: Error de Stripe al procesar {customer_id}: {e}", exc_info=True)
            except Exception as e:
                logger.error(f"Webhook {event_type}: Error inesperado al procesar {customer_id}: {e}", exc_info=True)


        elif event_type == 'invoice.payment_failed':
            # Falló el pago de la factura (renovación fallida)
             try:
                invoice = data_object
                customer_id = invoice.customer
                subscription_id = invoice.subscription

                if subscription_id:
                    profile = UserProfile.objects.get(stripe_customer_id=customer_id)

                    # Actualizar estado local (ej: 'past_due')
                    # Stripe actualizará el estado de la suscripción, el evento
                    # 'customer.subscription.updated' también se disparará.
                    # Podemos confiar en ese evento o actualizar aquí también.
                    profile.subscription_status = 'past_due' # O el estado que corresponda
                    profile.save()

                    logger.warning(f"Pago fallido procesado para Customer {customer_id}, Sub {subscription_id}. Perfil actualizado a past_due.")
                    # ENVIAR NOTIFICACIÓN AL USUARIO para que actualice su método de pago
                    # send_payment_failed_email.delay(profile.user.id)

             except UserProfile.DoesNotExist:
                logger.error(f"Webhook {event_type}: UserProfile no encontrado para customer {customer_id}")
             except Exception as e:
                logger.error(f"Webhook {event_type}: Error inesperado al procesar {customer_id}: {e}", exc_info=True)


        elif event_type == 'customer.subscription.updated':
            # Suscripción actualizada (cambio de plan, inicio/fin de prueba, marcada para cancelar, cambio de estado)
            try:
                subscription = data_object
                customer_id = subscription.customer
                profile = UserProfile.objects.get(stripe_customer_id=customer_id)

                # Actualizar todos los detalles relevantes en el perfil
                profile.update_subscription_details(subscription)

                logger.info(f"Suscripción actualizada procesada para Customer {customer_id}, Sub {subscription.id}. Perfil actualizado.")
                # Podrías notificar cambios de plan o si cancel_at_period_end cambia

            except UserProfile.DoesNotExist:
                logger.error(f"Webhook {event_type}: UserProfile no encontrado para customer {customer_id}")
            except Exception as e:
                logger.error(f"Webhook {event_type}: Error inesperado al procesar {customer_id}: {e}", exc_info=True)


        elif event_type == 'customer.subscription.deleted':
            # Suscripción eliminada/cancelada definitivamente
             try:
                subscription = data_object
                customer_id = subscription.customer
                profile = UserProfile.objects.get(stripe_customer_id=customer_id)

                # Limpiar/actualizar detalles de la suscripción en el perfil
                profile.clear_subscription_details()

                logger.info(f"Suscripción eliminada procesada para Customer {customer_id}, Sub {subscription.id}. Perfil actualizado a cancelado.")
                # Podrías enviar un email de confirmación de cancelación final

             except UserProfile.DoesNotExist:
                logger.error(f"Webhook {event_type}: UserProfile no encontrado para customer {customer_id}")
             except Exception as e:
                logger.error(f"Webhook {event_type}: Error inesperado al procesar {customer_id}: {e}", exc_info=True)

        elif event_type == 'customer.subscription.trial_will_end':
             # El periodo de prueba está por terminar (útil para recordatorios)
             try:
                 subscription = data_object
                 customer_id = subscription.customer
                 profile = UserProfile.objects.get(stripe_customer_id=customer_id)

                 # Enviar recordatorio al usuario
                 logger.info(f"Prueba por terminar para Customer {customer_id}, Sub {subscription.id}.")
                 # send_trial_ending_reminder_email.delay(profile.user.id)

             except UserProfile.DoesNotExist:
                logger.error(f"Webhook {event_type}: UserProfile no encontrado para customer {customer_id}")
             except Exception as e:
                logger.error(f"Webhook {event_type}: Error inesperado al procesar {customer_id}: {e}", exc_info=True)


        else:
            # Evento no manejado
            logger.info(f"Webhook no manejado: {event_type}, Event ID: {event.id}")
            pass # Ignorar otros eventos si no son relevantes ahora

        # 3. Confirmar recepción a Stripe
        # Es crucial devolver 200 OK para que Stripe sepa que lo recibiste
        # y no siga reintentando enviarlo. Incluso si hubo un error al procesar
        # internamente, usualmente devuelves 200 (y logueas el error) a menos
        # que sea un error temporal que Stripe debería reintentar.
        return Response(status=status.HTTP_200_OK)


class MembersSubscriptionsOverviewView(APIView):
    """
    Devuelve solo métricas agregadas:
    - total_members: número total de miembros con alguna suscripción registrada
    - total_active_members: número total de miembros con suscripción activa o en trial
    - total_inactive_members: número total de miembros con suscripción no activa
    - total_new_subscribers_this_month: número total de miembros nuevos con suscripción creada en el mes actual
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Inicio del mes actual (en zona temporal del servidor)
        now = timezone.now()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Base queryset
        qs = MembershipSubscription.objects.all()

        # Miembros totales (distintos perfiles con al menos una suscripción)
        total_members = qs.values('user_profile').distinct().count()

        # Activos por flag is_active o por estado en ['active', 'trialing']
        active_statuses = ['active', 'trialing']
        active_members_qs = qs.filter(models.Q(is_active=True) | models.Q(status__in=active_statuses))
        total_active_members = active_members_qs.values('user_profile').distinct().count()

        # Inactivos = miembros totales - activos (evita doble conteo si hay múltiples suscripciones)
        total_inactive_members = max(total_members - total_active_members, 0)

        # Nuevos suscriptores en el mes actual (miembros únicos con suscripción creada este mes)
        new_this_month_qs = qs.filter(created_at__gte=month_start)
        total_new_subscribers_this_month = new_this_month_qs.values('user_profile').distinct().count()

        data = {
            'total_members': total_members,
            'total_active_members': total_active_members,
            'total_inactive_members': total_inactive_members,
            'total_new_subscribers_this_month': total_new_subscribers_this_month,
        }
        return Response(data, status=status.HTTP_200_OK)


class MembersListView(APIView):
    """
    Lista de miembros con:
    - user_id
    - full_name
    - email
    - became_member_at (fecha en que se convirtió en miembro: primera suscripción)
    - plan_name (nombre del plan Nobilis actual o 'inactive' si no está activo)
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Perfiles que tienen al menos una suscripción
        profiles_qs = (
            UserProfile.objects
            .filter(subscriptions__isnull=False)
            .select_related('user')
            .prefetch_related(
                models.Prefetch(
                    'subscriptions',
                    queryset=MembershipSubscription.objects.select_related('plan').order_by('-created_at')
                )
            )
            .annotate(became_member_at=Min('subscriptions__created_at'))
            .distinct()
        )

        active_statuses = ['active', 'trialing']
        results = []
        for profile in profiles_qs:
            user = profile.user
            # Seleccionar la suscripción "actual" desde las prefeteadas: la más reciente activa/trialing
            subs = list(getattr(profile, 'subscriptions').all())
            current_sub = next((s for s in subs if (getattr(s, 'is_active', False) or getattr(s, 'status', None) in active_statuses)), None)
            is_active = False
            plan_name = 'inactive'
            if current_sub:
                sub_status = getattr(current_sub, 'status', None)
                is_active = getattr(current_sub, 'is_active', False) or (sub_status in active_statuses)
                if is_active and getattr(current_sub, 'plan', None):
                    plan_name = getattr(current_sub.plan, 'title', 'inactive') or 'inactive'
            results.append({
                'user_id': getattr(user, 'id', None),
                'full_name': f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip(),
                'email': getattr(user, 'email', None),
                'became_member_at': getattr(profile, 'became_member_at', None),
                'plan_name': plan_name,
            })

        # Orden opcional por became_member_at desc si se desea
        results.sort(key=lambda x: (x['became_member_at'] is not None, x['became_member_at']), reverse=True)
        return Response(results, status=status.HTTP_200_OK)


class PlanNobilis(generics.ListAPIView):
    serializer_class = PlanNobilisSerializer
    permission_classes = [permissions.AllowAny]

    def list(self, request, *args, **kwargs):
        queryset = Plan.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        response_data = {
            'success': True,
            'message': 'list of nobilis plan',
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class PlanDetailView(generics.RetrieveAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanNobilisSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = {
            'status': True,
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)


class PlanPricesView(generics.RetrieveAPIView):
    queryset = Plan.objects.all()
    serializer_class = PlanNobilisPriceSerializer
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        response_data = {
            'status': True,
            'message': 'plan price',
            'data': serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)

class AccountOverviewView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        profile = None  # Inicializar perfil
        profile_picture_url = None  # Inicializar URL de imagen de perfil

        # 1. Obtener Datos Básicos del Usuario
        user_data = {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': getattr(user, 'role_code', None),
            # Puedes añadir más campos del User si los necesitas
        }

        # 2. Obtener Datos de la Suscripción
        subscription_data = None  # Inicializar datos de suscripción

        try:
            profile = get_object_or_404(UserProfile, user=user)
            # Construir URL absoluta de la foto de perfil si existe
            try:
                if getattr(profile, 'profile_picture', None) and getattr(profile.profile_picture, 'url', None):
                    profile_picture_url = request.build_absolute_uri(profile.profile_picture.url)
            except Exception:
                profile_picture_url = None

            subscription_id = profile.stripe_subscription_id

            if not subscription_id:
                # No hay ID de suscripción guardado
                subscription_data = None #"status": None, "message": "No subscription found."}
            else:
                # Intentar obtener datos frescos de Stripe
                try:
                    stripe_subscription = stripe.Subscription.retrieve(
                        subscription_id,
                        expand=['plan.product', 'default_payment_method']
                    )

                    # Opcional: Auto-corrección (como en SubscriptionStatusView)
                    # ... (código de comparación y llamada a profile.update_subscription_details) ...
                    local_period_end_ts = int(profile.subscription_current_period_end.timestamp()) if profile.subscription_current_period_end else None
                    stripe_period_end_ts = getattr(stripe_subscription, 'current_period_end', None)
                    stripe_status = getattr(stripe_subscription, 'status', None)
                    stripe_cancel_at_period_end = getattr(stripe_subscription, 'cancel_at_period_end', False)

                    if (profile.subscription_status != stripe_status or
                        local_period_end_ts != stripe_period_end_ts or
                        profile.cancel_at_period_end != stripe_cancel_at_period_end):
                           logger.warning(f"Discrepancia detectada en overview para sub {subscription_id}. Actualizando perfil.")
                           profile.update_subscription_details(stripe_subscription)


                    # Serializar los datos frescos de Stripe
                    serializer = SubscriptionStatusSerializer(stripe_subscription)
                    subscription_data = serializer.data

                except stripe.error.InvalidRequestError as e:
                    # ID local es inválido/eliminado en Stripe
                    logger.warning(f"Stripe sub retrieve falló en overview para ID local {subscription_id} (User {user.id}): {e}. Limpiando datos locales.")
                    if profile: # Asegurarse que tenemos perfil antes de limpiar
                       profile.clear_subscription_details()
                    subscription_data = {"status": "inactive", "message": "Subscription reference invalid."}
                except stripe.error.StripeError as e:
                    # Otro error de Stripe API
                    logger.error(f"Error de API Stripe recuperando sub {subscription_id} en overview (User {user.id}): {e}", exc_info=True)
                    # Decidir qué devolver: ¿error? ¿datos locales? ¿null?
                    # Devolver null o un estado de error es más seguro que datos locales potencialmente desactualizados.
                    subscription_data = {"status": "error", "message": "Could not retrieve subscription details."}


        except UserProfile.DoesNotExist:
             # Si el perfil no existe, no podemos obtener datos de suscripción
             logger.error(f"UserProfile no encontrado para usuario autenticado {user.id} en overview")
             subscription_data = {"status": "error", "message": "User profile not found."}
        except Exception as e:
            # Error inesperado obteniendo perfil o procesando
            logger.error(f"Error inesperado en AccountOverviewView para user {user.id}: {e}", exc_info=True)
            # Podríamos devolver un error 500 aquí, o intentar devolver al menos los datos del usuario
            subscription_data = {"status": "error", "message": "An unexpected error occurred."}

        # Añadir la URL de la foto de perfil al bloque de usuario
        user_data['profile_picture'] = profile_picture_url

        response_data = {
            "user": user_data,
            "subscription": subscription_data  # Será el objeto serializado o un estado/mensaje
        }

        return Response(response_data, status=status.HTTP_200_OK)


class InvitationListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        user = request.user
        if not getattr(user, 'is_admin', False):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        from membership.models import UserInvitation
        qs = UserInvitation.objects.filter(invited_by=user).order_by('-created_at')
        serializer = UserInvitationSerializer(qs, many=True)
        return Response({'status': True, 'data': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        user = request.user
        if not getattr(user, 'is_admin', False):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        serializer = UserInvitationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            inv = serializer.save()
            return Response({'status': True, 'data': UserInvitationSerializer(inv).data}, status=status.HTTP_201_CREATED)
        return Response({'status': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class ShippingAddressView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = ShippingAddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user.shipping


class DependentsListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        User = get_user_model()
        dependents_qs = User.objects.filter(invited_by=request.user).order_by('-date_joined')
        serializer = DependentUserSerializer(dependents_qs, many=True)
        return Response({
            'status': True,
            'count': len(serializer.data),
            'data': serializer.data
        }, status=status.HTTP_200_OK)


class IsAdminOrReadOnly(permissions.BasePermission):
    """Allow read-only access to authenticated users; write access only to admins."""
    def has_permission(self, request, view):
        if request.method in ('GET', 'HEAD', 'OPTIONS'):
            return request.user and request.user.is_authenticated
        # For write methods, require admin
        return request.user and request.user.is_authenticated and getattr(request.user, 'is_admin', False)


class IntroductionCatalogListCreateView(generics.ListCreateAPIView):
    queryset = IntroductionCatalog.objects.all().order_by('-created_at')
    serializer_class = IntroductionCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]


class IntroductionCatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IntroductionCatalog.objects.all()
    serializer_class = IntroductionCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]


class IntroductionStatusListCreateView(generics.ListCreateAPIView):
    queryset = IntroductionStatus.objects.all().order_by('status_name')
    serializer_class = IntroductionStatusSerializer
    permission_classes = [IsAdminOrReadOnly]


class IntroductionStatusDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = IntroductionStatus.objects.all()
    serializer_class = IntroductionStatusSerializer
    permission_classes = [IsAdminOrReadOnly]


class InvolvedOrAdmin(permissions.BasePermission):
    """Allow access if user is admin or involved (from_user or to_user)."""
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_admin', False):
            return True
        return (obj.from_user_id == user.id) or (obj.to_user_id == user.id)


class MemberIntroductionListCreateView(generics.ListCreateAPIView):
    serializer_class = MemberIntroductionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = MemberIntroduction.objects.all().order_by('-created_at')
        if getattr(user, 'is_admin', False):
            return qs
        return qs.filter(models.Q(from_user=user) | models.Q(to_user=user))

    # --- Stripe payment subroutine ---
    def _process_introduction_payment(self, user, intro_type):
        """
        Creates and confirms a Stripe PaymentIntent for the selected introduction type.
        Uses user's saved Stripe customer and payment method. Returns a dict with success flag and
        optional error payload. Includes intro_type.stripe_product_id as a product identifier in metadata.
        """
        # If cost is empty or zero, nothing to charge
        cost = intro_type.cost or 0
        try:
            cost_decimal = Decimal(str(cost))
        except Exception:
            cost_decimal = Decimal('0')
        if cost_decimal <= 0:
            return {"success": True}

        # Fetch user profile to get Stripe IDs
        try:
            profile = UserProfile.objects.get(user=user)
        except UserProfile.DoesNotExist:
            return {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "error": {"detail": "User profile not found. Cannot process payment."}
            }

        if not profile.stripe_customer_id or not profile.stripe_payment_method_id:
            return {
                "success": False,
                "status": status.HTTP_400_BAD_REQUEST,
                "error": {"detail": "Missing Stripe payment setup. Please add a payment method."}
            }

        amount_cents = int((cost_decimal * 100).quantize(Decimal('1')))
        try:
            pi = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency='usd',
                customer=profile.stripe_customer_id,
                payment_method=profile.stripe_payment_method_id,
                confirm=True,
                off_session=True,
                description=f"Member introduction: {intro_type.title}",
                metadata={
                    'stripe_product_id': intro_type.stripe_product_id or '',
                    'introduction_type_id': str(intro_type.id),
                    'user_id': str(user.id),
                }
            )
            if pi.status == 'succeeded':
                return {"success": True}
            # If requires action or not succeeded
            return {
                "success": False,
                "status": status.HTTP_402_PAYMENT_REQUIRED,
                "error": {"detail": f"Payment not completed (status: {pi.status})."}
            }
        except stripe.error.CardError as e:
            return {
                "success": False,
                "status": status.HTTP_402_PAYMENT_REQUIRED,
                "error": {"detail": f"Card error: {e.user_message or str(e)}"}
            }
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error processing introduction payment for user {user.id}: {e}", exc_info=True)
            return {
                "success": False,
                "status": status.HTTP_502_BAD_GATEWAY,
                "error": {"detail": "Stripe service error while processing payment."}
            }
        except Exception as e:
            logger.exception(f"Unexpected error processing introduction payment for user {user.id}: {e}")
            return {
                "success": False,
                "status": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error": {"detail": "Unexpected error while processing payment."}
            }

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        intro_type = serializer.validated_data.get('introduction_type')

        # Process payment before creating the record
        payment_result = self._process_introduction_payment(request.user, intro_type)
        if not payment_result.get('success'):
            return Response(payment_result.get('error'), status=payment_result.get('status', status.HTTP_400_BAD_REQUEST))

        # Payment succeeded or not required; proceed to create
        instance = serializer.save(from_user=request.user)
        output = self.get_serializer(instance)
        headers = self.get_success_headers(output.data)
        return Response(output.data, status=status.HTTP_201_CREATED, headers=headers)


class MemberIntroductionDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MemberIntroductionSerializer
    permission_classes = [permissions.IsAuthenticated, InvolvedOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = MemberIntroduction.objects.all()
        if getattr(user, 'is_admin', False):
            return qs
        return qs.filter(models.Q(from_user=user) | models.Q(to_user=user))


class ReferralOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if getattr(user, 'is_admin', False):
            return True
        return getattr(obj, 'created_by_id', None) == user.id


class InviteeQualificationCatalogListCreateView(generics.ListCreateAPIView):
    queryset = InviteeQualificationCatalog.objects.all().order_by('-created_at')
    serializer_class = InviteeQualificationCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]


class InviteeQualificationCatalogDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = InviteeQualificationCatalog.objects.all()
    serializer_class = InviteeQualificationCatalogSerializer
    permission_classes = [IsAdminOrReadOnly]


class MemberReferralListCreateView(generics.ListCreateAPIView):
    serializer_class = MemberReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = MemberReferral.objects.all().order_by('-created_at')
        if getattr(user, 'is_admin', False):
            return qs
        return qs.filter(created_by=user)

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class MemberReferralDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MemberReferralSerializer
    permission_classes = [permissions.IsAuthenticated, ReferralOwnerOrAdmin]

    def get_queryset(self):
        user = self.request.user
        qs = MemberReferral.objects.all()
        if getattr(user, 'is_admin', False):
            return qs
        return qs.filter(created_by=user)
