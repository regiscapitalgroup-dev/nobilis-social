from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from nsocial.managers import CustomUserManager
from api.models import LanguageCatalog
import datetime
from django.conf import settings
from django.core.exceptions import ValidationError

def validate_image_size(value):
    filesize = value.size
    megabyte_limit = 5.0
    if filesize > megabyte_limit * 1024 * 1024:
        raise ValidationError("Max file size is %sMB" % str(megabyte_limit))


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, verbose_name='Name')
    last_name = models.CharField(max_length=30, verbose_name='Last Name')
    is_staff = models.BooleanField(default=False, verbose_name='Is Staff')
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Date Joined')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self) -> str:
        return self.email
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')

    introduction_headline = models.TextField(max_length=220, null=True, blank=True)
    alias_title = models.CharField(max_length=50, null=True, blank=True)
    profile_picture = models.ImageField(default='default.jpg', upload_to='profile_pics', null=True, blank=True,
                                        validators=[validate_image_size])

    birthday = models.DateField(null=True, blank=True) #EncryptedDateField(null=True, blank=True) #
    phone_number = models.CharField(max_length=25, null=True, blank=True) #EncryptedCharField(max_length=50, null=True, blank=True)
    street = models.CharField(max_length=200, null=True, blank=True) #EncryptedCharField(max_length=250, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True) #EncryptedCharField(max_length=150, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True) #EncryptedCharField(max_length=15, null=True, blank=True)
    prefered_phone = models.BooleanField(default=False)
    prefered_email = models.BooleanField(default=False)
    languages = models.TextField(blank=True, null=True)

    biography = models.TextField(blank=True, null=True)

    # --- Campos de Suscripción (actualizados por webhooks/API) ---
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True) # ID de la suscripción activa/relevante
    subscription_status = models.CharField(max_length=20, blank=True, null=True) # ej: active, trialing, past_due, canceled
    subscription_current_period_end = models.DateTimeField(blank=True, null=True) # Fecha fin periodo actual (UTC)
    cancel_at_period_end = models.BooleanField(default=False)
    # --- Campos de Método de Pago Predeterminado (actualizados por API/webhooks) ---
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=100, blank=True, null=True) # El ID del PM por defecto
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        return f'{self.user} Profile'

    # --- Métodos Helper (útiles para webhooks y esta vista) ---
    def update_subscription_details(self, stripe_subscription):
        """Actualiza campos locales desde un objeto Subscription de Stripe."""
        self.stripe_subscription_id = stripe_subscription.id
        self.subscription_status = stripe_subscription.status
        self.cancel_at_period_end = stripe_subscription.cancel_at_period_end
        try:
            self.subscription_current_period_end = datetime.datetime.fromtimestamp(
                stripe_subscription.current_period_end, tz=datetime.timezone.utc
            )
        except (TypeError, ValueError):
             self.subscription_current_period_end = None
        # Podrías añadir lógica para plan_id si lo necesitas
        self.save()

    def clear_subscription_details(self):
         """Limpia campos cuando una suscripción se cancela/elimina."""
         self.stripe_subscription_id = None
         # Decide qué estado poner: 'canceled', 'deleted', None?
         self.subscription_status = 'canceled'
         self.subscription_current_period_end = None
         self.cancel_at_period_end = False
         self.save()


class SocialMediaProfile(models.Model):
    user_profile = models.ForeignKey('UserProfile', on_delete=models.CASCADE, related_name='social_media_profiles')
    platform_name = models.CharField(max_length=100)
    profile_url = models.URLField(max_length=255)

    def __str__(self):
        return f"{self.user_profile.user}'s {self.platform_name} Profile"

    class Meta:
        unique_together = ('user_profile', 'platform_name')


class PersonalDetail(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='personal_detail')
    hobbies = models.TextField(blank=True, null=True)
    interests = models.TextField(blank=True, null=True)

class Club(models.Model):
    personal_detail = models.ForeignKey(PersonalDetail, on_delete=models.CASCADE, related_name='clubs')
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

class ProfessionalProfile(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='professional_profile')
    industries = models.TextField(blank=True, null=True)
    professional_interest = models.TextField(blank=True, null=True)

class WorkPosition(models.Model):
    professional_profile = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='work_positions')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    from_year = models.CharField(max_length=10)
    to_year = models.CharField(max_length=10)

class Education(models.Model):
    professional_profile = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='education')
    university_name = models.CharField(max_length=255)
    carreer = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    from_year = models.CharField(max_length=10)
    to_year = models.CharField(max_length=10)

class BoardPosition(models.Model):
    professional_profile = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='on_board')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    from_year = models.CharField(max_length=10)
    to_year = models.CharField(max_length=10)

class NonProfitInvolvement(models.Model):
    professional_profile = models.ForeignKey(ProfessionalProfile, on_delete=models.CASCADE, related_name='non_profit_involvement')
    company = models.CharField(max_length=255)
    position = models.CharField(max_length=255)
    city = models.CharField(max_length=100)
    from_year = models.CharField(max_length=10)
    to_year = models.CharField(max_length=10)

class Recognition(models.Model):
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='recognition')
    # Usamos JSONField para almacenar listas de texto simple de forma flexible
    top_accomplishments = models.JSONField(default=list)
    additional_links = models.JSONField(default=list)

class Expertise(models.Model):
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='expertise')
    title = models.CharField(max_length=100)
    content = models.TextField()
    rate = models.CharField(max_length=50)


class UserVideo(models.Model):
    # Relación con el perfil: si se borra el perfil, se borran sus videos.
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='videos')

    # El archivo de video en sí.
    #video_file = models.FileField(upload_to='user_videos/')
    video_link = models.URLField(null=True, blank=True)

    # Campos adicionales para dar contexto al video.
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for {self.user_profile.user.username} - {self.title}"


class Experience(models.Model):
    title = models.CharField(max_length=255, verbose_name="Título de la Experiencia")
    photograph = models.ImageField(upload_to='experiences/', verbose_name="Fotografía")
    description = models.TextField(verbose_name="Descripción")
    city = models.CharField(max_length=100, verbose_name="Ciudad")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Precio")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Experiencia"
        verbose_name_plural = "Experiencias"
        ordering = ['-created_at']
