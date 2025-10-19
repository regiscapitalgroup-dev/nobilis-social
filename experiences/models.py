from django.db import models
from django.conf import settings
from nsocial.models import CustomUser

class Experience(models.Model):
    """
    Representa una experiencia ofrecida por un anfitrión.
    """
    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_experiences',
        verbose_name='Anfitrión'
    )
    title = models.CharField(max_length=255, verbose_name='Título de la Experiencia')
    city = models.CharField(max_length=100, verbose_name='Lugar/Ciudad')
    date = models.DateTimeField(verbose_name='Fecha y Hora')
    duration_in_minutes = models.PositiveIntegerField(verbose_name='Duración en Minutos')
    max_guests = models.PositiveIntegerField(verbose_name='Número de Invitados')
    cost = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='Costo')
    photo = models.ImageField(upload_to='experience_photos/', verbose_name='Foto Ilustrativa')
    stripe_product_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Stripe Product ID')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'"{self.title}" by {self.host.email}'

    class Meta:
        ordering = ['-date']

class Booking(models.Model):
    """
    Representa la reservación de una experiencia por parte de un usuario.
    """

    experience = models.ForeignKey(Experience, on_delete=models.CASCADE, related_name='bookings')
    guest = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='reservations')
    status = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Reservación de {self.guest.email} para "{self.experience.title}"'

    class Meta:
        unique_together = ('experience', 'guest') # Evita que un usuario reserve la misma experiencia dos veces