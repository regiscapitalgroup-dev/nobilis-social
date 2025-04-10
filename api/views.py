from waitinglist.models import WaitingList
from .models import InviteTmpToken
from api.serializers import WaitingListSerializer, SetNewPasswordSerializer, ChangePasswordSerializer, TokenSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .paginations import CustomPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
import requests


class WaitingListView(APIView):
    pagination_class = CustomPagination
    serializer_class = WaitingListSerializer
    permission_classes = [AllowAny]

    def get(self, request, format=None):
        waitinglist = WaitingList.objects.all().filter(status_waiting_list=0)
        serializer = WaitingListSerializer(waitinglist, many=True)
        return Response(serializer.data)
    
    def post(self, request):
        serializer = WaitingListSerializer(data=request.data)
        if serializer.is_valid():
            user = get_user_model()
            new_user = user.objects.create(email=serializer.validated_data["email"], 
                                           first_name=serializer.validated_data["first_name"], 
                                           last_name=serializer.validated_data["last_name"],
                                           is_active=False)
            new_user.set_password('secret')
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)    
    

class WaitingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    parser_classes = (CamelCaseJSONParser,)
    lookup_field = "pk"


class WaitingListInviteView(APIView):
    #permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        waitinglist = WaitingList.objects.get(pk=pk)
        if waitinglist:
            user = get_user_model()
            reciber_email = waitinglist.email
            waitinglist.status_waiting_list = 1
            waitinglist.save(update_fields=['status_waiting_list'])

            new_user = user.objects.get(email=reciber_email)

            if new_user:
                token = RefreshToken.for_user(new_user)
                invite = InviteTmpToken(user_email=reciber_email, user_token=token, user_id=new_user.id)
                invite.save()
 
            current_site = get_current_site(request).domain
            # relative_link = reverse('activate-account')
            absLink = 'http://{}activate-account/{}'.format(current_site, token)

            subject = "Invitación a Nobilis"
            message = f"""
                Te invitamos a la fiesta
                
                {absLink}
                """
            from_email = settings.EMAIL_HOST_USER

            send_mail(subject=subject, 
                      message=message, 
                      from_email=from_email, 
                      recipient_list=[reciber_email], 
                      fail_silently=False,
                      )
            return Response({'success': 'email was send'}, status=status.HTTP_200_OK)
        else:
            return Response({'error': 'email was not send'}, status=status.HTTP_400_BAD_REQUEST)
    

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
        print(refresh_token)
        invite = InviteTmpToken.objects.get(user_token=refresh_token)
        if invite:
            print(invite.user_email)
 
            obj = get_user_model()
            user = obj.objects.get(email=invite.user_email)
            if user:
                user.is_active = True
                user.set_password(new_password)
                user.save(update_fields=['password', 'is_active'])
                token = RefreshToken.for_user(user).access_token

                user_token = TokenSerializer(token)

                return Response({'success': user_token.data}, status=status.HTTP_200_OK)  
        else:
            print(invite)
            print("no existe")
        return Response(status=status.HTTP_400_BAD_REQUEST)
