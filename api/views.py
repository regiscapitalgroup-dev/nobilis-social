from waitinglist.models import WaitingList
from api.serializers import WaitingListSerializer
from rest_framework import generics, status
from rest_framework.response import Response
from djangorestframework_camel_case.parser import CamelCaseJSONParser
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from .paginations import CustomPagination


class WaitingListView(APIView, CustomPagination):
    def get(self, request):
        waitinglist = WaitingList.objects.all()
        result_page = self.paginate_queryset(waitinglist, request)
        serializer = WaitingListSerializer(result_page, many=True)
        return self.get_paginated_response(serializer.data) 
    
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

