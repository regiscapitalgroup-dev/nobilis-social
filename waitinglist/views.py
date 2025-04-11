from waitinglist.models import WaitingList
from waitinglist.serializers import WaitingListSerializer
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from api.paginations import CustomPagination
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.contrib.auth import get_user_model
from rest_framework import status, generics
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.sites.shortcuts import get_current_site
from api.models import InviteTmpToken


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

                token = RefreshToken.for_user(new_user)
                invite = InviteTmpToken(user_email=reciber_email, user_token=token, user_id=new_user.id)
                invite.save()
                current_site = get_current_site(request).domain
                # relative_link = reverse('activate-account')
                absLink = 'http://{}/activate-account/{}'.format(current_site, token)
                subject = "Invitación a Nobilis"
                message = f"""
                    You're invited! :)
                    
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
                return Response({'error': 'user alredy active'}, status=status.HTTP_303_SEE_OTHER)
        else:
            return Response({'error': 'email was not send'}, status=status.HTTP_400_BAD_REQUEST)