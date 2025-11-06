from django.db import models
from django.conf import settings
from nsocial.models import CustomUser


class ExperienceCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Experience Categories"


class ExperienceOptionalEnhancement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Experience Optional Enhancements"


class Experience(models.Model):
    AVAILABILITY_BY_DATE = 'by_date'
    AVAILABILITY_BY_REQUEST = 'by_request'
    AVAILABILITY_CHOICES = [
        (AVAILABILITY_BY_DATE, 'By Date'),
        (AVAILABILITY_BY_REQUEST, 'By Request'),
    ]

    title = models.CharField(max_length=100, verbose_name='Nombre de la Experiencia')
    itinerary = models.TextField(null=True, blank=True, verbose_name='Itinerario')
    what_is_included = models.TextField(null=True, blank=True, verbose_name='Lo que incluye')
    #avialabity (by date or request)
    #date = models.DateField(verbose_name='Date')
    duration = models.IntegerField(default=1, verbose_name='Duration')
    price_per_guest = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name='Precio por invitado')
    #optional enhancements
    category = models.ForeignKey(ExperienceCategory, null=True, blank=True, on_delete=models.PROTECT, related_name='experiences')
    location_address = models.CharField(max_length=200, null=True, blank=True, verbose_name="Location Address")
    arrival_notes = models.TextField(null=True, blank=True, verbose_name='Notas de llegada')
    public = models.BooleanField(default=False)

    guest_capacity_adults = models.PositiveIntegerField(default=0, verbose_name='Capacidad de invitados Adultos')
    guest_capacity_children = models.PositiveIntegerField(default=0, verbose_name='Capacidad de invitados niños')
    guest_capacity_infants = models.PositiveIntegerField(default=0, verbose_name='Capacidad de invitados infantes')

    important_information_guest = models.TextField(max_length=250, null=True, blank=True, verbose_name='Important information for guests')
    ideal_audience = models.TextField(max_length=250, null=True, blank=True, verbose_name='Ideal audience')

    host_presence = models.CharField(max_length=200, null=True, blank=True, verbose_name="Host Presence")
    optional_addicional_team_members = models.TextField(max_length=250, null=True, blank=True, verbose_name='Addicional Team Members')

    beneficiary_for_profit = models.BooleanField(default=False, null=True, blank=True, verbose_name='Beneficiary for Profit')
    #payout details

    cover_image = models.ImageField(upload_to='experience_photos/', null=True, blank=True, verbose_name='Cover Image')
    galery_image = models.ImageField(upload_to='experience_photos/', null=True, blank=True, verbose_name='Galery Image')
    optional_video_link = models.URLField(max_length=250, null=True, blank=True, verbose_name='Optional Video Link')

    host = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='hosted_experiences',
        verbose_name='Anfitrión',
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'"{self.title}" by {self.host.email}'

    class Meta:
        ordering = ['-created_at']

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