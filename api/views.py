from waitinglist.models import WaitingList
from api.serializers import WaitingListSerializer
from rest_framework import generics
from djangorestframework_camel_case.parser import CamelCaseJSONParser

       
class WaitingListView(generics.ListCreateAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    parser_classes = (CamelCaseJSONParser,)


class WaitingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    parser_classes = (CamelCaseJSONParser,)
    lookup_field = "pk"
