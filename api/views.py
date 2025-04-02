from waitinglist.models import WaitingList, Category, Motivation
from api.serializers import WaitingListSerializer, CategorySerializer, MotivationSerializer
from rest_framework import generics

       
class WaitingListView(generics.ListCreateAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer


class CategoryView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class MotivationView(generics.ListCreateAPIView):
    queryset = Motivation.objects.all()
    serializer_class = MotivationSerializer


class WaitingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = WaitingList.objects.all()
    serializer_class = WaitingListSerializer
    lookup_field = "pk"


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    lookup_field = "pk"


class MotivationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Motivation.objects.all()
    serializer_class = MotivationSerializer
    lookup_field = "pk"
