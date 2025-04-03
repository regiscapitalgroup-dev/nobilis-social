from waitinglist.models import WaitingList
from api.serializers import WaitingListSerializer
from rest_framework import generics

       
class WaitingListView(generics.ListCreateAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer


class WaitingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    lookup_field = "pk"

