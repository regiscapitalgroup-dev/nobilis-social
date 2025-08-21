from waitinglist.models import WaitingList
from waitinglist.serializers import WaitingListSerializer, ExistingUserSerializer
from rest_framework.response import Response
from rest_framework.views import APIView
from api.paginations import CustomPagination
from rest_framework.permissions import AllowAny
import uuid
from rest_framework import status, generics
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from api.models import InviteTmpToken
from django.core.exceptions import ObjectDoesNotExist


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
            if not new_user.is_active:
                token_uuid = uuid.uuid4()
                token = token_uuid.hex #RefreshToken.for_user(new_user)
                invite = InviteTmpToken(user_email=reciber_email, user_token=token, user_id=new_user.id)
                invite.save()
                current_site = 'https://main.d1rykkcgalxqn2.amplifyapp.com/auth'
                abslink = '{}/activate-account/{}/{}/'.format(current_site, token, new_user.first_name)
                subject = "Nobilis Invitation"
                message = f"""
                    You're invited! :)
                    
                    {abslink}
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
                return Response({'error': 'user alredy active'}, status=status.HTTP_303_SEE_OTHER)
        else:
            return Response({'error': 'email was not send'}, status=status.HTTP_400_BAD_REQUEST)
        

class UserExistsView(APIView):
    serializer_class = ExistingUserSerializer
    permission_classes = [AllowAny]    

    def post(self, request):
        waitinglist = WaitingList.objects.all()
        serializer = ExistingUserSerializer(data=request.data)
        if serializer.is_valid(): 
            try:
                user = waitinglist.get(email=serializer.validated_data["email"])
                if user:
                    return Response({'error': 'user already exists.'}, status=status.HTTP_409_CONFLICT)
            except ObjectDoesNotExist:
                return Response({'message':'user does not exist'}, status=status.HTTP_200_OK)
        return Response({'error': 'email was not send'}, status=status.HTTP_400_BAD_REQUEST)
