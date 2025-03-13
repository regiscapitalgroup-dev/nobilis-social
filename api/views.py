from waitinglist.models import WaitingList
from .serializers import WaitingListSerializer
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status


@api_view(['GET', 'POST'])
def waitinglistView(request):
    if request.method == 'GET':
        waitinglist = WaitingList.objects.all().filter(status_waiting_list=0)
        serializer = WaitingListSerializer(waitinglist, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    elif request.method == 'POST':
        serializer = WaitingListSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
def waitinglistDetailView(request, pk):
    try:
        waitinglist = WaitingList.objects.get(pk=pk)
    except WaitingList.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        serializer = WaitingListSerializer(waitinglist)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    elif request.method == 'PUT':
        serializer = WaitingListSerializer(waitinglist, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        waitinglist.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
