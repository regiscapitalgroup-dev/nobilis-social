from api.models import InviteTmpToken
from .serializers import (
    CustomUserSerializer,
    CurrentUserSerializer,
    UserProfileSerializer,
    SocialMediaProfileSerializer,
    FullProfileSerializer,
    UserVideoSerializer,
    ExperienceSerializer,
    RoleSerializer,
    AdminProfileSerializer,
    AdminProfileBasicSerializer,
    AdminProfileConfidentialSerializer,
    AdminProfileBiographySerializer,
)
from .models import CustomUser, UserProfile, SocialMediaProfile, Experience, Role, Recognition, Expertise
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
import requests
from rest_framework.views import APIView
from django.urls import reverse
from nsocial.serializers import ChangePasswordSerializer, SetNewPasswordSerializer, PasswordResetConfirmSerializer
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]


class CurrentUserView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly,]    
    def get(self, request):
        serializer = CurrentUserSerializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ChangePasswordView(generics.GenericAPIView):
    serializer_class = ChangePasswordSerializer

    def put(self, request, pk):
        password = request.data["password"]
        new_password = request.data["new_password"]

        obj = get_user_model().objects.get(pk=pk)
        if not obj.check_password(raw_password=password):
            return Response({'error': 'password not match'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            obj.set_password(new_password)
            obj.save()
            return Response({'success': 'password changed successfully'}, status=status.HTTP_200_OK)


class SetNewPasswordView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def put(self, request):
        new_password = request.data["new_password"]
        refresh_token = request.data["refresh_token"]
        invite = InviteTmpToken.objects.get(user_token=refresh_token)
        if invite:
            obj = get_user_model()
            user = obj.objects.get(email=invite.user_email)
            if user:
                user.is_active = True
                user.set_password(new_password)
                user.save(update_fields=['password', 'is_active'])
                
                data = {'email': invite.user_email, 'password': new_password}
                current_site = get_current_site(request).domain
                relative_link = reverse('token_obtain_pair')

                r = requests.post(f'http://{current_site}{relative_link}', data=data) 
                invite.delete()
                if r.status_code == 200:
                    return Response(r.json(), status=status.HTTP_200_OK)  
        else:
            return Response({'error': 'invalid invitation'}, status=status.HTTP_403_FORBIDDEN)
        return Response(status=status.HTTP_400_BAD_REQUEST)


class UserProfileView(generics.RetrieveUpdateAPIView):
    parser_classes = [MultiPartParser, FormParser]
    queryset = UserProfile.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        try:
            obj = UserProfile.objects.get(user=self.request.user)
            self.check_object_permissions(self.request, obj)
            return obj
        except UserProfile.DoesNotExist:
            #from django.http import Http404
            #raise Http404
            return Response({
                "success": False,
                "message": "User profile not found."
            }, status=status.HTTP_404_NOT_FOUND)
        
    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            response.data = {
                "success": True,
                "message": "Profile updated successful."
            }
        return response


class ForgotMyPassword(APIView):   
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({'error': 'email is required.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'If an account exists with this email, reset instructions will be sent.'}, status=status.HTTP_200_OK)
        
        token_generator = PasswordResetTokenGenerator()
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        token = token_generator.make_token(user)
        
        reset_link = f"https://main.d1rykkcgalxqn2.amplifyapp.com/reset-password/{uidb64}/{token}/"

        subject = 'Nobilis: Reset your Password'
        message = (
            f"Hello {user.first_name},\n\n"
            f"Click the link below to reset your password.:\n"
            f"{reset_link}\n\n"
            f"If you did not request this, please ignore this email.\n"
            "The link will expire in 1 hour.\n\n"
            "Thank You."
        )
        try:
            send_mail(subject, message, settings.ADMIN_USER_EMAIL, [user.email])
        except Exception as e:
            print(f"Error sending email: {e}")
            return Response({
                "success": False,
                "message": "There was a problem sending the email."
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response({'detail': 'If an account exists with this email, reset instructions will be sent.'}, status=status.HTTP_200_OK)    


class PasswordResetConfirmView(APIView):
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(serializer.validated_data['user']))
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            user = None

        token_generator = PasswordResetTokenGenerator()
        if user is not None and token_generator.check_token(user, serializer.validated_data['token']):
            p = serializer.validated_data['password']
            user.set_password(p)
            user.save()

            data = {"email": user, 'password': p}
            current_site = get_current_site(request).domain
            relative_link = reverse('token_obtain_pair')
            r = requests.post(f'https://{current_site}{relative_link}', data=data) 
            if r.status_code == 200:
                return Response(r.json(), status=status.HTTP_200_OK)
        else:
            return Response({'error': 'The reset link is invalid or has expired.'}, status=status.HTTP_400_BAD_REQUEST)


class SocialMediaProfileListCreateView(generics.ListCreateAPIView):

    serializer_class = SocialMediaProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):

        return SocialMediaProfile.objects.filter(user_profile=self.request.user.profile)

    def get_serializer(self, *args, **kwargs):

        if isinstance(kwargs.get('data', {}), list):
            kwargs['many'] = True

        return super().get_serializer(*args, **kwargs)

    def perform_create(self, serializer):
        # Asigna automáticamente el perfil del usuario actual al crear un nuevo objeto
        serializer.save(user_profile=self.request.user.profile)

class SocialMediaProfileRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    """
    Vista para ver, actualizar y eliminar un perfil de red social específico.
    """
    serializer_class = SocialMediaProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # El usuario solo puede afectar a sus propios perfiles sociales
        return SocialMediaProfile.objects.filter(user_profile=self.request.user.profile)


class AdminProfileView(generics.RetrieveUpdateAPIView):
    """
    View to retrieve/update only postal_address and often_in, including relatives list (read-only).
    """
    serializer_class = AdminProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class AdminProfileBasicView(generics.RetrieveUpdateAPIView):
    """
    Endpoint: /api/admin-profile/basic/
    Allows GET and PUT/PATCH to update basic admin profile fields:
    alias_title, introduction_headline, postal_address, guiding_principle,
    annual_limits_introduction, receive_reports, languages, introductions (setter).
    """
    serializer_class = AdminProfileBasicSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class AdminProfileConfidentialView(generics.RetrieveUpdateAPIView):
    """
    Endpoint: /api/admin-profile/confidential/
    Allows PUT/PATCH to update confidential fields of the admin profile:
    birthday, phone_number, contact_methods, address, city_country, cities_of_interest,
    partner {name, surname}, and relatives (replace list).
    """
    serializer_class = AdminProfileConfidentialSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile


class FullProfileView(generics.RetrieveUpdateAPIView):
    """
    Vista para ver y actualizar el perfil completo del usuario autenticado.
    """
    serializer_class = FullProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        # Buscamos/creamos el perfil del usuario autenticado
        profile, _ = UserProfile.objects.get_or_create(user=self.request.user)
        return profile

    def get_serializer_context(self):
        ctx = super().get_serializer_context()
        raw = self.request.query_params.get('fresh_subscription')
        # Acepta 1/true/yes (case-insensitive) como verdadero
        fresh = str(raw).lower() in ('1', 'true', 'yes') if raw is not None else False
        ctx['fresh_subscription'] = fresh
        return ctx

class UserVideoListCreateView(generics.ListCreateAPIView):
    serializer_class = UserVideoSerializer
    permission_classes = [IsAuthenticated]
    # Especificamos que esta vista acepta datos 'multipart/form-data'
    parser_classes = [MultiPartParser, FormParser]

    def get_queryset(self):
        # Mostramos solo los videos del usuario que hace la petición
        return self.request.user.profile.videos.all().order_by('-uploaded_at')

    def perform_create(self, serializer):
        # Asignamos el perfil del usuario automáticamente al subir un video
        serializer.save(user_profile=self.request.user.profile)


class UserVideoDestroyView(generics.DestroyAPIView):
    serializer_class = UserVideoSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # El usuario solo puede eliminar sus propios videos
        return self.request.user.profile.videos.all()


class ExperienceListView(generics.ListAPIView):
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    permission_classes = [AllowAny]


class IsAdminOrReadOnly(generics.GenericAPIView):
    def has_permission(self, request, view=None):
        # Note: we can't subclass BasePermission without importing; implement inline check in views instead
        return True


class RoleListCreateView(generics.ListCreateAPIView):
    queryset = Role.objects.all().order_by('code')
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        # Authenticated users can list roles
        return super().get(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        # Only admins can create
        if not getattr(request.user, 'is_admin', False):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def patch(self, request, *args, **kwargs):
        if not getattr(request.user, 'is_admin', False):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return super().patch(request, *args, **kwargs)

    def put(self, request, *args, **kwargs):
        if not getattr(request.user, 'is_admin', False):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return super().put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        if not getattr(request.user, 'is_admin', False):
            return Response({'detail': 'Forbidden'}, status=status.HTTP_403_FORBIDDEN)
        return super().delete(request, *args, **kwargs)



class ProfilePictureUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request):
        file_obj = request.FILES.get('profile_picture') or request.data.get('profile_picture')
        if not file_obj:
            return Response({'detail': 'profile_picture is required'}, status=status.HTTP_400_BAD_REQUEST)
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.profile_picture = file_obj
        profile.save(update_fields=['profile_picture'])
        # Devolver la ruta (URL) donde quedó accesible la imagen
        path = getattr(profile.profile_picture, 'url', None)
        return Response({"status": "ok", "path": path}, status=status.HTTP_200_OK)

    def patch(self, request):
        return self.put(request)


class AdminProfileBiographyView(APIView):
    """
    Endpoint: /api/admin-profile/biography/
    Accepts PUT/PATCH with JSON:
    {
        "biography": "...",
        "urls": ["https://...", ...]
    }
    - Updates the current user's UserProfile.biography if provided.
    - Replaces the user's UserVideo list with the provided URLs if provided.
    Returns the resulting biography and urls.
    """
    permission_classes = [IsAuthenticated]

    def _update(self, request):
        serializer = AdminProfileBiographySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        # Update biography if present
        if 'biiology' in data:  # safeguard typo won't ever trigger; real key below
            pass
        if 'biography' in data:
            profile.biography = data.get('biography')
            profile.save(update_fields=['biography'])

        # Replace videos if urls provided
        urls = data.get('urls', None)
        if urls is not None:
            # Delete existing videos
            profile.videos.all().delete()
            # Create new videos preserving input order
            for url in urls:
                try:
                    profile.videos.create(video_link=url)
                except Exception:
                    # If a URL is malformed beyond URLField validation, skip silently
                    continue

        # Prepare response
        current_urls = list(profile.videos.order_by('id').values_list('video_link', flat=True))
        return Response({
            'biography': profile.biography,
            'urls': current_urls,
        }, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)



class RecognitionUpdateView(APIView):
    """
    Updates current user's Recognition via PUT/PATCH.
    Expected payload:
    {
      "recognition": [
        {"desc": "...", "url": "..."},
        ...
      ],
      "additional_links": ["https://...", ...]
    }
    - Saves `recognition` array as-is into Recognition.top_accomplishments
    - Saves `additional_links` into Recognition.additional_links
    """
    permission_classes = [IsAuthenticated]

    def _update(self, request):
        data = request.data or {}
        # Basic validation and normalization
        recog_list = data.get('recognition', None)
        links_list = data.get('additional_links', None)

        if recog_list is not None and not isinstance(recog_list, list):
            return Response({'detail': 'recognition must be an array'}, status=status.HTTP_400_BAD_REQUEST)
        if links_list is not None and not isinstance(links_list, list):
            return Response({'detail': 'additional_links must be an array'}, status=status.HTTP_400_BAD_REQUEST)

        # Optionally validate items shape
        if isinstance(recog_list, list):
            cleaned = []
            for item in recog_list:
                if not isinstance(item, dict):
                    continue
                desc = item.get('desc')
                url = item.get('url')
                # keep only keys of interest
                cleaned.append({'desc': desc, 'url': url})
            recog_list = cleaned

        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        recognition_obj, _ = Recognition.objects.get_or_create(user_profile=profile)

        updates = {}
        if recog_list is not None:
            recognition_obj.top_accomplishments = recog_list
            updates['top_accomplishments'] = recog_list
        if links_list is not None:
            recognition_obj.additional_links = links_list
            updates['additional_links'] = links_list

        if updates:
            # Save only if something provided
            recognition_obj.save()

        return Response({
            'top_accomplishments': recognition_obj.top_accomplishments,
            'additional_links': recognition_obj.additional_links,
        }, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)



class ExpertiseUpdateView(APIView):
    """
    Updates current user's Expertise via PUT/PATCH.
    Expected payload:
    {
      "expertise": [
        {"title": "...", "content": "...", "pricing": "200", "rate": "hr"},
        ...
      ]
    }
    - Replaces the user's expertise list with the provided items.
    - Associates all items to the current session user's UserProfile.
    """
    permission_classes = [IsAuthenticated]

    def _update(self, request):
        from decimal import Decimal, InvalidOperation

        payload = request.data or {}
        items = payload.get('expertise', None)

        if items is None:
            return Response({'detail': 'expertise is required'}, status=status.HTTP_400_BAD_REQUEST)
        if not isinstance(items, list):
            return Response({'detail': 'expertise must be an array'}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure user profile exists
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

        # Replace existing expertise entries
        profile.expertise.all().delete()

        saved = []
        for item in items:
            if not isinstance(item, dict):
                continue
            title = item.get('title')
            content = item.get('content')
            pricing_val = item.get('pricing', None)
            rate = item.get('rate')

            # If no fields provided, skip
            if title is None and content is None and pricing_val is None and rate is None:
                continue

            # Coerce pricing to Decimal or None
            pricing = None
            if pricing_val not in (None, ""):
                try:
                    pricing = Decimal(str(pricing_val))
                except (InvalidOperation, ValueError, TypeError):
                    pricing = None

            obj = Expertise.objects.create(
                user_profile=profile,
                title=title or "",
                content=content or "",
                pricing=pricing,
                rate=str(rate or "")
            )
            saved.append({
                'id': obj.id,
                'title': obj.title,
                'content': obj.content,
                'pricing': str(obj.pricing) if obj.pricing is not None else None,
                'rate': obj.rate,
            })

        return Response({'expertise': saved}, status=status.HTTP_200_OK)

    def put(self, request):
        return self._update(request)

    def patch(self, request):
        return self._update(request)
