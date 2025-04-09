from django.shortcuts import render
from .serializers import CustomUserSerializer, CurrentUserSerializer
from .models import CustomUser
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response


class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [AllowAny]


class CurrentUserView(generics.GenericAPIView):
    permission_classes = [IsAuthenticatedOrReadOnly,]    
    def get(self, request):
        serializer = CurrentUserSerializer(self.request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
