from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from membership.models import Plan, Subscription
from django.utils.decorators import method_decorator
from membership.serializers import PriceSerializer, SubscriptionCreateSerializer, SubscriptionSerializer, SubscriptionStatusSerializer
from nsocial.models import UserProfile
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
import logging
import stripe
from django.utils import timezone
import datetime
from django.conf import settings


stripe.api_key = settings.STRIPE_SECRET_KEY


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
                    expand=['latest_invoice.payment_intent'],
                )

                # 6. Manejar la respuesta de la suscripción
                response_data = {
                    'subscription_id': subscription.id,
                    'status': subscription.status,
                }
                if subscription.status == 'incomplete' and subscription.latest_invoice.payment_intent.status == 'requires_action':
                     response_data['client_secret'] = subscription.latest_invoice.payment_intent.client_secret

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


class SubscriptionStatusView(APIView):
    """
    Obtiene el estado de la suscripción activa o de prueba del usuario actual.
    """
    permission_classes = [permissions.IsAuthenticated] # Requiere que el usuario esté logueado

    def get(self, request, *args, **kwargs):
        user = request.user
        try:
            # 1. Obtener el perfil del usuario y su stripe_customer_id
            profile = get_object_or_404(UserProfile, user=user)
            customer_id = profile.stripe_customer_id

            if not customer_id:
                # Si no hay customer_id, el usuario nunca inició un proceso de pago/suscripción
                return Response({"status": "no_customer_id", "message": "Usuario no encontrado en Stripe."}, status=status.HTTP_404_NOT_FOUND)

            # 2. Buscar suscripciones del cliente en Stripe
            # Buscamos todas para poder determinar el estado más relevante
            # Expandimos el plan (precio + producto) y el método de pago por defecto
            subscriptions = stripe.Subscription.list(
                customer=customer_id,
                status='all', # Obtenemos todas para filtrar luego
                expand=[
                    'data.plan.product',
                    'data.default_payment_method' # Opcional: info de la tarjeta usada
                ],
                limit=10 # Limita por si acaso, usualmente un usuario tiene pocas
            )

            # 3. Filtrar y seleccionar la suscripción relevante
            active_subscription = None
            relevant_subscription_data = None

            # Prioridad: Activa o en Prueba
            for sub in subscriptions.data:
                if sub.status in ['active', 'trialing']:
                    active_subscription = sub
                    break # Encontramos la más importante

            if active_subscription:
                serializer = SubscriptionStatusSerializer(active_subscription)
                relevant_subscription_data = serializer.data
                # Añadimos un campo extra para claridad en el frontend
                relevant_subscription_data['effective_status'] = active_subscription.status
            else:
                # Si no hay activa/prueba, podríamos opcionalmente buscar la última cancelada/incompleta
                # para dar contexto, o simplemente decir que no hay suscripción activa.
                # Por simplicidad, diremos que no hay activa:
                return Response({"status": "inactive", "message": "No se encontró una suscripción activa o de prueba."}, status=status.HTTP_200_OK)


            return Response(relevant_subscription_data, status=status.HTTP_200_OK)

        except UserProfile.DoesNotExist:
             return Response({"status": "no_profile", "message": "Perfil de usuario no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except stripe.error.StripeError as e:
            # Manejo de errores de Stripe
            # Podría ser 'customer not found' si el ID es inválido/antiguo
            return Response(
                {"error": f"Error al obtener estado de Stripe: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR # O un código más específico
            )
        except Exception as e:
            # Manejo de otros errores
            # Loggear el error
            return Response(
                {"error": "Ocurrió un error inesperado."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
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
                           cancel_date = datetime.datetime.fromtimestamp(sub.current_period_end, tz=datetime.timezone.utc)
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
    

logger = logging.getLogger(__name__) # Configura logging en settings.py

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
