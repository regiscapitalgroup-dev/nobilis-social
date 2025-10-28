from waitinglist.models import WaitingList, RejectionReason
from nsocial.models import CustomUser
from waitinglist.serializers import (
    WaitingListSerializer,
    RejectWaitingListSerializer,
    WaitingListAdminListSerializer,
    RejectionReasonSerializer,
    ExistingUserSerializer
)
from rest_framework.response import Response
from django.db import transaction
from notification.models import Notification
from rest_framework.permissions import AllowAny
import uuid
from nsocial.models import Role
from rest_framework import status, generics, viewsets
from rest_framework.decorators import action
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from moderation.views import IsAdminRole
from rest_framework.views import APIView
from django.core.exceptions import ObjectDoesNotExist
from api.models import InviteTmpToken
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

class WaitingListView(generics.ListCreateAPIView):
    throttle_classes = [AnonRateThrottle]
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data.get('email')

        # Busca si ya existe una entrada APROBADA con este email
        # Usamos la constante del modelo WaitingList
        already_approved = WaitingList.objects.filter(
            email=email,
            status=WaitingList.STATUS_APPROVED  # Usa la constante del modelo
        ).exists()

        if already_approved:
            # Si ya existe y está aprobada, devuelve un error 409 Conflict
            return Response(
                {"error": "This email has already been registered and approved."},
                status=status.HTTP_409_CONFLICT
            )

        # Si no existe una entrada aprobada, procede a crear la nueva entrada
        # Llama a perform_create para guardar y notificar (como ya lo hacía)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    # perform_create ahora solo guarda y notifica (ya no necesita validar)
    def perform_create(self, serializer):
        instance = serializer.save()

        # Lógica de notificación a administradores (sin cambios)
        try:
            admin_users = list(CustomUser.objects.filter(role__is_admin=True))  #

            if not admin_users:
                print("Advertencia: No se encontraron usuarios administradores para notificar.")
                return

            waitinglist_content_type = ContentType.objects.get_for_model(instance)

            for admin in admin_users:
                Notification.objects.create(
                    recipient=admin,
                    actor=None,
                    verb=f"{instance.first_name} {instance.last_name} has joined the waiting list",
                    target_content_type=waitinglist_content_type,
                    target_object_id=instance.pk
                )  #
            print(f"Notificaciones enviadas a {len(admin_users)} administradores.")

        except Exception as e:
            print(f"Error al intentar crear notificaciones para WaitingList: {e}")

    # def perform_create(self, serializer):
    #     instance = serializer.save()
    #
    #     try:
    #         admin_users = list(CustomUser.objects.filter(role__is_admin=True))
    #
    #         if not admin_users:
    #             print("Advertencia: No se encontraron usuarios administradores para notificar.")
    #             return
    #
    #         waitinglist_content_type = ContentType.objects.get_for_model(instance)
    #
    #         for admin in admin_users:
    #             Notification.objects.create(
    #                 recipient=admin,
    #                 actor=None,
    #                 verb=f"{instance.first_name} {instance.last_name} has joined the waiting list", #
    #                 target_content_type=waitinglist_content_type, #
    #                 target_object_id=instance.pk #
    #             )
    #         print(f"Notificaciones enviadas a {len(admin_users)} administradores.")
    #
    #     except Exception as e:
    #         print(f"Error al intentar crear notificaciones para WaitingList: {e}")

class WaitingListAdminViewSet(viewsets.ReadOnlyModelViewSet):
    throttle_classes = [UserRateThrottle]
    queryset = WaitingList.objects.all().order_by('-id') # Corrected ordering field if needed
    permission_classes = [IsAdminRole]
    pagination_class = None

    # Use get_serializer_class to select the serializer
    def get_serializer_class(self):
        if self.action == 'list':
            return WaitingListAdminListSerializer
        if self.action == 'reject':
            return RejectWaitingListSerializer
        # For 'approve' or 'retrieve' (if enabled), use the basic one
        return WaitingListSerializer

    # Pass context for 'assigned' field in list view
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    # --- approve action logic ---
    @action(detail=True, methods=['post'])
    @transaction.atomic
    def approve(self, request, pk=None):
        waiting_entry = self.get_object()

        if waiting_entry.status != WaitingList.STATUS_PENDING:
            return Response({'error': 'This request has already been processed.'}, status=status.HTTP_400_BAD_REQUEST)

        if CustomUser.objects.filter(email=waiting_entry.email).exists():
            waiting_entry.status = WaitingList.STATUS_REJECTED
            waiting_entry.save()
            return Response({'error': 'A user with this email already exists in the system.'}, status=status.HTTP_400_BAD_REQUEST)

        # Assuming Role ID 2 is 'FINAL USER'. Get the Role instance.
        try:
             # Make sure the Role model is imported: from nsocial.models import Role
            default_role_instance = Role.objects.get(pk=2)
        except Role.DoesNotExist:
             return Response({'error': 'Default role (ID=2) not found.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        user = CustomUser.objects.create_user(
            email=waiting_entry.email,
            password=None,
            first_name=waiting_entry.first_name,
            last_name=waiting_entry.last_name,
            is_active=False,
            role=default_role_instance # Assign the Role instance
        )

        token_uuid = uuid.uuid4()
        token = token_uuid.hex
        invite = InviteTmpToken(user_email=user.email, user_token=token, user_id=user.id)
        invite.save()
        current_site = settings.CURRENT_SITE # Assuming CURRENT_SITE is defined in settings
        # Construct URL based on frontend needs, using the actual token
        abslink = f'{current_site}/activate-account/{token}/{user.first_name}/' # Example structure

        subject = 'You have been accepted into Nobilis!'
        message = (
            f"Hello {user.first_name},\n\n"
            f"Congratulations! Your application to join Nobilis has been approved.\n\n"
            f"To activate your account and set your password, please click the following link:\n"
            f"{abslink}\n\n"
            f"Welcome to the community!\n\n"
            f"Greetings,\nThe Nobilis Team"
        )
        try:
            # Make sure ADMIN_USER_EMAIL is defined in settings
            send_mail(subject, message, settings.ADMIN_USER_EMAIL, [user.email])
        except Exception as e:
            print(f"Error sending activation email to {user.email}: {e}")
            # Consider transaction rollback or specific error handling
            return Response({'error': 'User created but activation email failed to send.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        waiting_entry.status = WaitingList.STATUS_APPROVED
        waiting_entry.save()

        return Response({'success': f'User {user.email} approved and activation email sent.'}, status=status.HTTP_200_OK)

    # --- reject action logic ---
    @action(detail=True, methods=['post'], serializer_class=RejectWaitingListSerializer)
    def reject(self, request, pk=None):
        waiting_entry = self.get_object()

        if waiting_entry.status != WaitingList.STATUS_PENDING:
            return Response({'error': 'This request has already been processed.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reason = serializer.validated_data['rejection_reason']
        notes = serializer.validated_data['notes'] # If you add 'notes' back

        waiting_entry.status = WaitingList.STATUS_REJECTED
        waiting_entry.rejection_reason = reason
        waiting_entry.notes = notes # If you add 'notes' back
        waiting_entry.save()

        subject = 'Update on your application at Nobilis'
        message = (
            f"Hello {waiting_entry.first_name}\n\n"
            f"Unfortunately, we have rejected your request to join Nobilis.\n\n"
            # Optional: Include reason f"Reason: {reason}\n\n"
            f"Greetings,\nThe Nobilis Team"
        )
        try:
            # Make sure ADMIN_USER_EMAIL is defined in settings
            send_mail(subject, message, settings.ADMIN_USER_EMAIL, [waiting_entry.email])
        except Exception as e:
             print(f"Error sending rejection email to {waiting_entry.email}: {e}")
             # Decide if this error should affect the response

        return Response({'success': f'Request for {waiting_entry.email} rejected.'}, status=status.HTTP_200_OK)


# class WaitingListAdminViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = WaitingList.objects.all().order_by('-created_at')
#     permission_classes = [IsAdminRole]
#
#     def get_serializer_class(self):
#         if self.action == 'list':
#             return WaitingListAdminListSerializer # Usa el nuevo para GET /admin/
#         if self.action == 'reject':
#             return RejectWaitingListSerializer # Usa el de rechazo para la acción reject
#         # Para otras acciones como 'retrieve' (si la habilitas) o 'approve',
#         # puedes usar el original o ninguno si no devuelven datos complejos.
#         return WaitingListSerializer # Serializer por defecto para retrieve, etc.
#
#     # --- ASEGURA PASAR EL CONTEXTO AL SERIALIZER ---
#     # Es necesario para que get_assigned funcione
#     def get_serializer_context(self):
#         """
#         Añade el objeto request al contexto del serializer.
#         """
#         context = super().get_serializer_context()
#         context['request'] = self.request
#         return context
#
#     # ... (acciones 'approve' y 'reject' existentes) ...
#     @action(detail=True, methods=['post'])
#     @transaction.atomic
#     def approve(self, request, pk=None):
#         # ... (código existente de approve) ...
#         pass # Solo para estructura
#
#     @action(detail=True, methods=['post'], serializer_class=RejectWaitingListSerializer)
#     def reject(self, request, pk=None):
#          # ... (código existente de reject) ...
#         pass # Solo para estructura
#
#
# class WaitingListAdminViewSet(viewsets.ReadOnlyModelViewSet):
#     queryset = WaitingList.objects.all().order_by('-created_at')
#     serializer_class = WaitingListSerializer
#     permission_classes = [IsAdminRole] # Solo Admins
#
#     @action(detail=True, methods=['post'])
#     @transaction.atomic
#     def approve(self, request, pk=None):
#         waiting_entry = self.get_object()
#
#         if waiting_entry.status != WaitingList.STATUS_PENDING:
#             return Response({'error': 'This request has already been processed.'}, status=status.HTTP_400_BAD_REQUEST)
#
#         if CustomUser.objects.filter(email=waiting_entry.email).exists():
#             waiting_entry.status = WaitingList.STATUS_REJECTED
#             waiting_entry.save()
#             return Response({'error': 'A user with this email already exists in the system.'}, status=status.HTTP_400_BAD_REQUEST)
#
#         default_role = 2 #FINAL USER
#
#         user = CustomUser.objects.create_user(
#             email=waiting_entry.email,
#             password=None,
#             first_name=waiting_entry.first_name,
#             last_name=waiting_entry.last_name,
#             is_active=False,
#             role=default_role
#         )
#
#         token_uuid = uuid.uuid4()
#         token = token_uuid.hex
#         invite = InviteTmpToken(user_email=user.email, user_token=token, user_id=user.id)
#         invite.save()
#         current_site = settings.CURRENT_SITE
#         abslink = '{}/activate-account/{}/{}/'.format(current_site, token, user.first_name)
#
#         # 6. Enviar correo de invitación/activación
#         subject = 'You have been accepted into Nobilis!'
#         message = (
#             f"Hello {user.first_name},\n\n"
#             f"Congratulations! Your application to join Nobilis has been approved.\n\n"
#             f"To activate your account and set your password, please click the following link:\n"
#             f"{abslink}\n\n"
#             f"Welcome to the community!\n\n"
#             f"Greetings,\nThe Nobilis Team"
#         )
#         try:
#             send_mail(subject, message, settings.ADMIN_USER_EMAIL, [user.email])
#         except Exception as e:
#             print(f"Error al enviar email de activación a {user.email}: {e}")
#             # Considera si quieres revertir la transacción aquí o solo loggear
#             return Response({'error': 'User created but activation email failed to send.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
#
#         # 7. Actualizar estado en WaitingList
#         waiting_entry.status = WaitingList.STATUS_APPROVED
#         waiting_entry.save()
#
#         return Response({'success': f'User {user.email} approved and activation email sent.'}, status=status.HTTP_200_OK)
#
#     @action(detail=True, methods=['post'], serializer_class=RejectWaitingListSerializer)
#     def reject(self, request, pk=None):
#         waiting_entry = self.get_object()
#
#         # 1. Validar estado
#         if waiting_entry.status != WaitingList.STATUS_PENDING:
#             return Response({'error': 'This request has already been processed.'}, status=status.HTTP_400_BAD_REQUEST)
#
#         serializer = self.get_serializer(data=request.data)
#         serializer.is_valid(raise_exception=True)
#         reason = serializer.validated_data['rejection_reason']
#         notes = serializer.validated_data['notes']
#
#         # 2. Actualizar estado
#         waiting_entry.status = WaitingList.STATUS_REJECTED
#         waiting_entry.rejection_reason = reason
#         waiting_entry.notes = notes
#         waiting_entry.save()
#
#         # (Opcional) Enviar correo de rechazo
#         subject = 'Update on your application at Nobilis'
#         message = (
#             f"Hello {waiting_entry.first_name}\n\n"
#             f"Unfortunately, we have rejected your request to join Nobilis.\n\n"
#
#             f"Greetings,\nThe Nobilis Team"
#         )
#         send_mail(subject, message, settings.ADMIN_USER_EMAIL, [waiting_entry.email])
#
#         return Response({'success': f'Request for {waiting_entry.email} rejected.'}, status=status.HTTP_200_OK)



class WaitingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    parser_classes = (CamelCaseJSONParser,)
    lookup_field = "pk"


class RejectionReasonListView(generics.ListAPIView):
    queryset = RejectionReason.objects.all()
    serializer_class = RejectionReasonSerializer
    permission_classes = [AllowAny]



class UserExistsView(APIView):
    serializer_class = ExistingUserSerializer
    permission_classes = [AllowAny]

    def post(self, request):
        waitinglist = WaitingList.objects.all()
        serializer = ExistingUserSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = waitinglist.get(email=serializer.validated_data["email"], status=WaitingList.STATUS_APPROVED)
                if user:
                    return Response({
                        'success': False,
                        'message': 'User already exists.'
                    }, status=status.HTTP_409_CONFLICT)
            except ObjectDoesNotExist:
                return Response({
                    'success': False,
                    'message':'User does not exist'
                }, status=status.HTTP_200_OK)
        return Response({
            'success': False,
            'message': 'email was not send'
        }, status=status.HTTP_400_BAD_REQUEST)