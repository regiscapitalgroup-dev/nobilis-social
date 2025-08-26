from api.models import InviteTmpToken
from .serializers import CustomUserSerializer, CurrentUserSerializer, UserProfileSerializer
from .models import CustomUser, UserProfile
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly, IsAuthenticated
from rest_framework.response import Response
import requests
from rest_framework.views import APIView
from django.urls import reverse
from nsocial.serializers import ChangePasswordSerializer, SetNewPasswordSerializer, PasswordResetConfirmSerializer
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.sites.shortcuts import get_current_site


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
