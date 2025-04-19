# tests.py (en tu app, por ejemplo 'subscriptions')

from django.test import TestCase # O APITestCase si prefieres
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.test import APITestCase # Usaremos esta por conveniencia con APIClient
from unittest.mock import patch, MagicMock # La librería clave para mocking
import stripe # Para referenciar tipos de error de Stripe

# Importa tus modelos relevantes
from nsocial.models import UserProfile # ¡Ajusta esta ruta a tu app de perfiles!
# Asume que tus vistas están en 'views.py' dentro de la misma app
# Si no, ajusta la ruta en los decoradores @patch

User = get_user_model()

# --- Pruebas para CreateSubscriptionView (Llamada Única) ---

class CreateSubscriptionViewTests(APITestCase):

    def setUp(self):
        """ Configuración inicial para cada prueba """
        # Crear usuario y perfil de prueba
        self.user = User.objects.create_user(email='test@example.com', password='testpassword')
        # Asegúrate de que el perfil se cree (puede ser via signals o aquí directamente)
        # Si no usas signals, créalo explícitamente:
        self.profile = UserProfile.objects.create(user=self.user)

        # Autenticar el cliente de prueba de DRF
        self.client.force_authenticate(user=self.user)

        # URL del endpoint a probar
        self.url = reverse('create-subscription') # Usa el 'name' de tu URLConf

        # Datos válidos de ejemplo para enviar en el POST
        self.valid_payload = {
            'payment_method_id': 'pm_card_visa', # Un ID de PM de prueba válido de Stripe
            'price_id': 'price_basic_monthly' # Un ID de Precio de prueba válido de Stripe
        }

    # --- Escenario 1: Éxito - Cliente Nuevo ---
    # Usamos @patch para interceptar las llamadas a Stripe DENTRO de tu archivo views.py
    # ¡¡IMPORTANTE!! Ajusta 'your_app_name.views.stripe' a la ruta correcta donde importas stripe en tus vistas
    @patch('membership.views.stripe.Subscription.create')
    @patch('membership.views.stripe.PaymentMethod.retrieve')
    @patch('membership.views.stripe.Customer.create')
    def test_create_subscription_new_customer_success(self, mock_customer_create, mock_pm_retrieve, mock_sub_create):
        """ Prueba la creación exitosa de suscripción para un usuario sin customer_id previo. """

        # --- 1. Configurar los Mocks ---
        # Configurar lo que devolverá stripe.Customer.create
        mock_customer = MagicMock()
        mock_customer.id = 'cus_test_new'
        mock_customer_create.return_value = mock_customer

        # Configurar lo que devolverá stripe.PaymentMethod.retrieve (para guardar brand/last4)
        mock_pm = MagicMock()
        mock_pm.id = self.valid_payload['payment_method_id']
        mock_pm.type = 'card'
        mock_pm.card.brand = 'visa'
        mock_pm.card.last4 = '4242'
        mock_pm_retrieve.return_value = mock_pm

        # Configurar lo que devolverá stripe.Subscription.create
        mock_sub = MagicMock()
        mock_sub.id = 'sub_test_new'
        mock_sub.status = 'active'
        # Simular la estructura anidada si tu código la necesita (ej: para client_secret)
        mock_sub.latest_invoice.payment_intent.status = 'succeeded' # Asumir pago inmediato ok
        mock_sub_create.return_value = mock_sub

        # --- 2. Realizar la Llamada a la API ---
        response = self.client.post(self.url, self.valid_payload, format='json')

        # --- 3. Hacer Aserciones (Verificaciones) ---
        # Verificar código de estado HTTP (201 Created)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verificar datos en la respuesta JSON
        self.assertEqual(response.data['subscription_id'], 'sub_test_new')
        self.assertEqual(response.data['status'], 'active')
        self.assertNotIn('client_secret', response.data) # Porque el status fue 'active'

        # Verificar que las funciones de Stripe mockeadas fueron llamadas como se esperaba
        # Customer.create DEBE haber sido llamado (porque era cliente nuevo)
        mock_customer_create.assert_called_once()
        # Verificar argumentos específicos si es necesario
        call_args, call_kwargs = mock_customer_create.call_args
        self.assertEqual(call_kwargs['email'], self.user.email)
        self.assertEqual(call_kwargs['payment_method'], self.valid_payload['payment_method_id'])
        self.assertIn('default_payment_method', call_kwargs['invoice_settings'])

        # PaymentMethod.retrieve DEBE haber sido llamado para guardar detalles
        mock_pm_retrieve.assert_called_once_with(self.valid_payload['payment_method_id'])

        # Subscription.create DEBE haber sido llamado
        mock_sub_create.assert_called_once_with(
            customer='cus_test_new',
            items=[{'price': self.valid_payload['price_id']}],
            expand=['latest_invoice.payment_intent']
        )

        # Verificar el estado de la base de datos (UserProfile actualizado)
        self.profile.refresh_from_db() # Recargar datos desde la BD de prueba
        self.assertEqual(self.profile.stripe_customer_id, 'cus_test_new')
        self.assertEqual(self.profile.stripe_subscription_id, 'sub_test_new')
        self.assertEqual(self.profile.subscription_status, 'active')
        self.assertEqual(self.profile.stripe_payment_method_id, self.valid_payload['payment_method_id'])
        self.assertEqual(self.profile.card_brand, 'visa')
        self.assertEqual(self.profile.card_last4, '4242')

    # --- Escenario 2: Éxito - Cliente Existente ---
    @patch('membership.views.stripe.Subscription.create')
    @patch('membership.views.stripe.PaymentMethod.retrieve')
    @patch('membership.views.stripe.Customer.modify') # Mockear modify
    @patch('membership.views.stripe.PaymentMethod.attach') # Mockear attach
    @patch('membership.views.stripe.Customer.create') # Mockear create aunque no se llamará
    def test_create_subscription_existing_customer_success(self, mock_customer_create, mock_pm_attach, mock_customer_modify, mock_pm_retrieve, mock_sub_create):
        """ Prueba la creación exitosa si el usuario ya tiene un customer_id. """
        # --- 1. Configurar Estado Inicial y Mocks ---
        # Establecer un customer_id existente en el perfil
        existing_customer_id = 'cus_test_existing'
        self.profile.stripe_customer_id = existing_customer_id
        self.profile.save()

        # Configurar mocks (similar a antes, pero ahora esperamos attach y modify)
        mock_pm = MagicMock(id=self.valid_payload['payment_method_id'], type='card', card=MagicMock(brand='mastercard', last4='5678'))
        mock_pm_retrieve.return_value = mock_pm

        mock_sub = MagicMock(id='sub_test_existing', status='active', latest_invoice=MagicMock(payment_intent=MagicMock(status='succeeded')))
        mock_sub_create.return_value = mock_sub

        # --- 2. Realizar la Llamada a la API ---
        response = self.client.post(self.url, self.valid_payload, format='json')

        # --- 3. Hacer Aserciones ---
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['subscription_id'], 'sub_test_existing')

        # Verificar llamadas a Stripe: create NO debe llamarse, attach y modify SÍ
        mock_customer_create.assert_not_called()
        mock_pm_attach.assert_called_once_with(self.valid_payload['payment_method_id'], customer=existing_customer_id)
        mock_customer_modify.assert_called_once_with(
            existing_customer_id,
            invoice_settings={'default_payment_method': self.valid_payload['payment_method_id']},
        )
        mock_pm_retrieve.assert_called_once_with(self.valid_payload['payment_method_id'])
        mock_sub_create.assert_called_once_with(
             customer=existing_customer_id, # Usa el ID existente
             items=[{'price': self.valid_payload['price_id']}],
             expand=['latest_invoice.payment_intent']
        )

        # Verificar BD (Customer ID no cambia, PM sí, Sub ID sí)
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.stripe_customer_id, existing_customer_id) # Sigue siendo el mismo
        self.assertEqual(self.profile.stripe_subscription_id, 'sub_test_existing')
        self.assertEqual(self.profile.card_brand, 'mastercard') # Datos del nuevo PM mockeado
        self.assertEqual(self.profile.card_last4, '5678')

    # --- Escenario 3: Error - Falla la Creación del Cliente ---
    @patch('membership.views.stripe.Subscription.create') # Mockear aunque no se alcanzará
    @patch('membership.views.stripe.PaymentMethod.retrieve') # Mockear aunque no se alcanzará
    @patch('membership.views.stripe.Customer.create')
    def test_create_subscription_customer_create_error(self, mock_customer_create, mock_pm_retrieve, mock_sub_create):
        """ Prueba el manejo de error si stripe.Customer.create falla. """
        # Configurar mock para lanzar una excepción de Stripe
        mock_customer_create.side_effect = stripe.error.InvalidRequestError("Invalid source.", "source")

        # Realizar llamada
        response = self.client.post(self.url, self.valid_payload, format='json')

        # Verificar respuesta de error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        # Verificar que no se intentó crear la suscripción
        mock_sub_create.assert_not_called()
        # Verificar que el perfil NO se actualizó con un customer_id
        self.profile.refresh_from_db()
        self.assertIsNone(self.profile.stripe_customer_id)

    # --- Escenario 4: Error - Falla la Creación de la Suscripción ---
    @patch('membership.views.stripe.Subscription.create')
    @patch('membership.views.stripe.PaymentMethod.retrieve')
    @patch('membership.views.stripe.Customer.create')
    def test_create_subscription_subscription_create_error(self, mock_customer_create, mock_pm_retrieve, mock_sub_create):
        """ Prueba el manejo de error si stripe.Subscription.create falla. """
        # Configurar mocks para Customer y PM (asumimos éxito hasta la suscripción)
        mock_customer = MagicMock(id='cus_test_for_sub_fail')
        mock_customer_create.return_value = mock_customer
        mock_pm = MagicMock(id=self.valid_payload['payment_method_id'], type='card', card=MagicMock(brand='visa', last4='4242'))
        mock_pm_retrieve.return_value = mock_pm

        # Configurar mock de suscripción para lanzar error
        mock_sub_create.side_effect = stripe.error.CardError("Card declined.", "card_declined", "declined")

        # Realizar llamada
        response = self.client.post(self.url, self.valid_payload, format='json')

        # Verificar respuesta de error
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['code'], 'card_declined') # El código de error de Stripe

        # Verificar que el perfil SÍ se actualizó con customer_id y PM (porque esos pasos fueron "exitosos")
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.stripe_customer_id, 'cus_test_for_sub_fail')
        self.assertEqual(self.profile.card_brand, 'visa')
        self.assertIsNone(self.profile.stripe_subscription_id) # La suscripción no se creó

    # --- Escenario 5: Error - Input Inválido ---
    def test_create_subscription_invalid_payload(self):
        """ Prueba la respuesta si faltan datos en el payload. """
        invalid_payload = {'price_id': 'price_valid'} # Falta payment_method_id
        response = self.client.post(self.url, invalid_payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('payment_method_id', response.data) # El serializer debe indicar el error

    # --- Escenario 6: Error - No Autenticado ---
    def test_create_subscription_unauthenticated(self):
        """ Prueba la respuesta si el usuario no está autenticado. """
        self.client.logout() # O simplemente no llamar a force_authenticate
        response = self.client.post(self.url, self.valid_payload, format='json')
        # El código exacto puede depender de tu config de autenticación/permisos por defecto
        self.assertTrue(response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])


    # ... PODRÍAS AÑADIR MÁS PRUEBAS ...
    # - Para el caso de suscripción incompleta (status='incomplete', requiere acción -> client_secret)
    # - Para errores específicos al adjuntar/modificar PM en cliente existente.