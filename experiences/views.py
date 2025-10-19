# experiences/views.py

from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils import timezone
from .models import Experience, Booking
from .serializers import ExperienceSerializer, BookingSerializer

class ExperienceViewSet(viewsets.ModelViewSet):
    """
    ViewSet para gestionar Experiencias.
    """
    queryset = Experience.objects.all()
    serializer_class = ExperienceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Filtra las experiencias:
        - Muestra solo las futuras para el listado general.
        """
        if self.action == 'list':
            return Experience.objects.filter(date__gte=timezone.now())
        return super().get_queryset()

    def perform_create(self, serializer):
        """Asigna al usuario actual como anfitrión de la experiencia."""
        serializer.save(host=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-experiences')
    def my_experiences(self, request):
        """
        Endpoint para que un anfitrión vea las experiencias que ha creado.
        """
        experiences = Experience.objects.filter(host=request.user)
        serializer = self.get_serializer(experiences, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='history')
    def history(self, request):
        """
        Endpoint para ver el historial de experiencias pasadas en las que
        el usuario participó como invitado.
        """
        past_bookings = Booking.objects.filter(
            guest=request.user,
            experience__date__lt=timezone.now(),
            status='confirmed'
        )
        serializer = BookingSerializer(past_bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='book')
    def book(self, request, pk=None):
        """
        Endpoint para que un usuario solicite reservar una experiencia.
        """
        experience = self.get_object()
        if experience.host == request.user:
            return Response({'error': 'No puedes reservar tu propia experiencia.'}, status=status.HTTP_400_BAD_REQUEST)

        booking, created = Booking.objects.get_or_create(
            experience=experience,
            guest=request.user
        )

        if not created:
            return Response({'error': 'Ya has solicitado una reservación para esta experiencia.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'success': 'Solicitud de reservación enviada.'}, status=status.HTTP_201_CREATED)


class BookingViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet para que los anfitriones vean y gestionen las solicitudes de reservación.
    """
    serializer_class = BookingSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """
        Solo el anfitrión de la experiencia puede ver sus reservaciones.
        """
        return Booking.objects.filter(experience__host=self.request.user)

    @action(detail=True, methods=['post'])
    def confirm(self, request, pk=None):
        """Confirma una solicitud de reservación."""
        booking = self.get_object()
        booking.status = 'confirmed'
        booking.save()
        return Response({'status': 'Reservación confirmada.'})

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancela una solicitud de reservación."""
        booking = self.get_object()
        booking.status = 'cancelled'
        booking.save()
        return Response({'status': 'Reservación cancelada.'})

