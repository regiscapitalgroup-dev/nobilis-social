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


class Role(models.Model):
    code = models.SlugField(max_length=50, unique=True, verbose_name='Code')
    name = models.CharField(max_length=100, verbose_name='Name')
    description = models.TextField(blank=True, default='', verbose_name='Description')
    is_admin = models.BooleanField(default=False, verbose_name='Is Admin')

    def __str__(self) -> str:
        return self.name or self.code

    class Meta:
        verbose_name = 'Role'
        verbose_name_plural = 'Roles'


class CustomUser(AbstractBaseUser, PermissionsMixin):
    username = None
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, verbose_name='Name')
    last_name = models.CharField(max_length=30, verbose_name='Last Name')
    role = models.ForeignKey('Role', null=True, blank=True, on_delete=models.SET_NULL, related_name='users', verbose_name='Role')
    invited_by = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='invited_users', verbose_name='Invited By')
    is_staff = models.BooleanField(default=False, verbose_name='Is Staff')
    is_active = models.BooleanField(default=True, verbose_name='Is Active')
    date_joined = models.DateTimeField(default=timezone.now, verbose_name='Date Joined')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self) -> str:
        return self.email

    @property
    def role_code(self):
        return getattr(self.role, 'code', None)

    @property
    def is_admin(self):
        # Superusers are always considered admins
        return bool(getattr(self.role, 'is_admin', False) or self.is_superuser)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
    introduction_headline = models.TextField(max_length=220, null=True, blank=True)
    alias_title = models.CharField(max_length=50, null=True, blank=True)
    profile_picture = models.ImageField(default='profile_pics/default.jpg', upload_to='profile_pics', null=True, blank=True,
                                        validators=[validate_image_size])
    birthday = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=25, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    prefered_phone = models.BooleanField(default=False)
    prefered_email = models.BooleanField(default=False)
    languages = models.TextField(blank=True, null=True)
    bio_presentation = models.CharField(max_length=250, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    pic_footer = models.CharField(max_length=250, blank=True, null=True)
    #admin profile v1
    life_partner_name  = models.CharField(max_length=150, blank=True, null=True)
    life_partner_lastname = models.CharField(max_length=150, blank=True, null=True)
    postal_address = models.TextField(null=True, blank=True)
    often_in = models.TextField(null=True, blank=True)
    guiding_principle = models.CharField(max_length=50, null=True, blank=True)
    annual_limits_introduction = models.IntegerField(null=True, blank=True, default=0)
    receive_reports = models.BooleanField(default=False)

    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True)
    subscription_status = models.CharField(max_length=20, blank=True, null=True)
    subscription_current_period_end = models.DateTimeField(blank=True, null=True)
    cancel_at_period_end = models.BooleanField(default=False)

    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    stripe_payment_method_id = models.CharField(max_length=100, blank=True, null=True)
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        return f'{self.user} Profile'

    # --- Métodos Helper (útiles para webhooks y esta vista) ---
    def update_subscription_details(self, stripe_subscription):
        """Actualiza caché del perfil y la `MembershipSubscription` asociada."""
        from membership.models import Plan, MembershipSubscription
        # Perfil (caché)
        self.stripe_subscription_id = stripe_subscription.id
        self.subscription_status = getattr(stripe_subscription, 'status', None)
        self.cancel_at_period_end = getattr(stripe_subscription, 'cancel_at_period_end', False)
        try:
            ts = getattr(stripe_subscription, 'current_period_end', None)
            self.subscription_current_period_end = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc) if ts else None
        except Exception:
            self.subscription_current_period_end = None
        self.save()

        # Sincronizar/crear fila en MembershipSubscription
        price_id = None
        try:
            items = getattr(stripe_subscription, 'items', None)
            if items and getattr(items, 'data', None):
                price_id = items.data[0].price.id
        except Exception:
            pass

        plan_obj = Plan.objects.filter(stripe_plan_id=price_id).first() if price_id else None

        sub_obj, _ = MembershipSubscription.objects.update_or_create(
            stripe_subscription_id=stripe_subscription.id,
            defaults={
                'user_profile': self,
                'plan': plan_obj,
                'status': getattr(stripe_subscription, 'status', ''),
                'cancel_at_period_end': getattr(stripe_subscription, 'cancel_at_period_end', False),
                'current_period_end': self.subscription_current_period_end,
                'is_active': getattr(stripe_subscription, 'status', '') in ['active', 'trialing'] and not getattr(stripe_subscription, 'canceled_at', None),
            }
        )

        # Actualizar puntero de conveniencia
        self.current_subscription = sub_obj
        self.save(update_fields=['current_subscription'])

    def clear_subscription_details(self):
         """Limpia campos cuando una suscripción se cancela/elimina."""
         self.stripe_subscription_id = None
         self.subscription_status = 'canceled'
         self.subscription_current_period_end = None
         self.cancel_at_period_end = False
         self.current_subscription = None
         self.save()


# class AdminProfile(models.Model):
#     user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='profile')
#
#     introduction_headline = models.TextField(max_length=220, null=True, blank=True)
#     alias_title = models.CharField(max_length=50, null=True, blank=True)
#     profile_picture = models.ImageField(default='default.jpg', upload_to='profile_pics', null=True, blank=True,
#                                         validators=[validate_image_size])
#
#     birthday = models.DateField(null=True, blank=True)
#     phone_number = models.CharField(max_length=25, null=True, blank=True)
#     residence_city = models.CharField(max_length=100, null=True, blank=True)
#     postal_code = models.CharField(max_length=10, null=True, blank=True)
#     prefered_phone = models.BooleanField(default=False)
#     prefered_email = models.BooleanField(default=False)
#     postal_address = models.TextField(null=True, blank=True)
#     often_in = models.TextField(null=True, blank=True)
#     languages = models.TextField(blank=True, null=True)
#     bio_presentation = models.CharField(max_length=250, blank=True, null=True)
#     biography = models.TextField(blank=True, null=True)
#     pic_footer = models.CharField(max_length=250, blank=True, null=True)
#     guiding_principle = models.CharField(max_length=50, null=True, blank=True)
#
#
#     def __str__(self):
#         return f'{self.user} Admin Profile'
#
#     class Meta:
#         verbose_name_plural = 'Admin Profiles'


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
    pricing = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, default=0)
    rate = models.CharField(max_length=50)


class UserVideo(models.Model):
    # Relación con el perfil: si se borra el perfil, se borran sus videos.
    user_profile = models.ForeignKey(UserProfile, on_delete=models.CASCADE, related_name='videos')

    # El archivo de video en sí.
    video_link = models.URLField(null=True, blank=True)

    # Campos adicionales para dar contexto al video.
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True, null=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Video for {self.user_profile.user.username} - {self.title}"


class Author(models.Model):
    name = models.CharField(max_length=255, verbose_name="Autor")
    photo_url = models.URLField(null=True, blank=True, verbose_name="Foto del Autor")

    def __str__(self):
        return self.name


class Experience(models.Model):
    title = models.CharField(max_length=255, verbose_name="Título de la Experiencia")
    authors = models.ManyToManyField(Author, related_name='experiences', blank=True)
    experience_photograph = models.URLField(null=True, blank=True)
    description = models.TextField(null=True, blank=True, verbose_name="Descripción")
    city = models.CharField(null=True, blank=True, max_length=100, verbose_name="Ciudad")
    price = models.DecimalField(null=True, blank=True, max_digits=10, decimal_places=2, verbose_name="Precio")
    is_new = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Experiencia"
        verbose_name_plural = "Experiencias"
        ordering = ['-created_at']



class UserIntroductionPreference(models.Model):
    """
    Relaciona un perfil de usuario con un único tipo del catálogo de introducciones
    que puede recibir. Se limita a un registro por perfil (OneToOne).
    """
    user_profile = models.OneToOneField(UserProfile, on_delete=models.CASCADE, related_name='introduction_preference')
    introduction_type = models.ForeignKey('membership.IntroductionCatalog', on_delete=models.PROTECT, related_name='user_introduction_preferences')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        try:
            return f"{self.user_profile.user.email} -> {getattr(self.introduction_type, 'name', self.introduction_type_id)}"
        except Exception:
            return f"Preference #{self.pk}"

    class Meta:
        verbose_name = 'User Introduction Preference'
        verbose_name_plural = 'User Introduction Preferences'
