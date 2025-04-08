from waitinglist.models import WaitingList
from api.serializers import WaitingListSerializer, SetNewPasswordSerializer, ChangePasswordSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .paginations import CustomPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.mail import send_mail
from django.conf import settings


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
    permission_classes = [IsAuthenticated]
    
    def put(self, request, pk):
        waitinglist = WaitingList.objects.get(pk=pk)
        if waitinglist:
            reciber_email = waitinglist.email
            waitinglist.status_waiting_list = 1
            waitinglist.save(update_fields=['status_waiting_list'])
            subject = "Invitación a Nobilis"
            message = f"""
                Te invitamos a la fiesta
                
                http://127.0.0.1:8000/api/v1/activate-account/{pk}/
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

    def put(self, request, pk):
        new_password = request.data["new_password"]
        obj = get_user_model().objects.get(pk=pk)
        if obj:
            obj.is_active = True
            obj.set_password(new_password)
            obj.save(update_fields=['password', 'is_active'])
            return Response({'success': 'user activation complete'}, status=status.HTTP_200_OK)
        return Response(status=400)
