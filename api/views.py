from waitinglist.models import WaitingList
from api.serializers import WaitingListSerializer
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.http import Http404


class WaitingListAPIView(APIView):
    def get(self, request):
        waitinglist = WaitingList.objects.all().filter(status_waiting_list=0)
        serializer = WaitingListSerializer(waitinglist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def post(self, request):
        serializer = WaitingListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class WaitingListDetailAPIView(APIView):
    def get_object(self, pk):
        try:
            return WaitingList.objects.get(pk=pk)
        except WaitingList.DoesNotExist:
            raise Http404
        
    def get(self, request, pk):
        waitinglist = self.get_object(pk)
        serializer = WaitingListSerializer(waitinglist)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request, pk):
        waitinglist = self.get_object(pk)
        serializer = WaitingListSerializer(waitinglist, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def delete(self, request, pk):
        waitinglist = self.get_object(pk)
        waitinglist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
