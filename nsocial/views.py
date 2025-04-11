from api.models import InviteTmpToken
from .serializers import CustomUserSerializer, CurrentUserSerializer
from .models import CustomUser
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
import requests
from django.urls import reverse
from nsocial.serializers import ChangePasswordSerializer, SetNewPasswordSerializer
from django.contrib.auth import get_user_model
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

