from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.utils import timezone
from nsocial.managers import CustomUserManager
import datetime
from django.conf import settings


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
    # ... otros campos como bio, profile_picture, dirección ...
    bio = models.TextField(blank=True)
    profile_picture = models.ImageField(default='default.jpg', upload_to='profile_pics')
    street = models.CharField(max_length=200, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    postal_code = models.CharField(max_length=10, null=True, blank=True)
    country = models.CharField(max_length=150, null=True, blank=True)
    # --- Campos relacionados con Stripe ---
    stripe_customer_id = models.CharField(max_length=100, blank=True, null=True)
    # --- Campos de Suscripción (actualizados por webhooks/API) ---
    stripe_subscription_id = models.CharField(max_length=100, blank=True, null=True) # ID de la suscripción activa/relevante
    subscription_status = models.CharField(max_length=20, blank=True, null=True) # ej: active, trialing, past_due, canceled
    subscription_current_period_end = models.DateTimeField(blank=True, null=True) # Fecha fin periodo actual (UTC)
    cancel_at_period_end = models.BooleanField(default=False)
    # --- Campos de Método de Pago Predeterminado (actualizados por API/webhooks) ---
    stripe_payment_method_id = models.CharField(max_length=100, blank=True, null=True) # El ID del PM por defecto
    card_brand = models.CharField(max_length=50, blank=True, null=True)
    card_last4 = models.CharField(max_length=4, blank=True, null=True)

    def __str__(self):
        return f'{self.user.username} Profile'

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

"""

class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    video = models.FileField(upload_to='videos/', null=True, blank=True)
    image = models.ImageField(upload_to='images/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='likes_posts', through='Like')

    def __str__(self):
        return f'{self.user.username} Post'

    
class Like(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)


class Follow(models.Model):
    follower = models.ForeignKey(User, on_delete=models.CASCADE, related_name='following')
    following = models.ForeignKey(User, on_delete=models.CASCADE, related_name='followers')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('follower', 'following')


class Comment(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.user.username} Commented on {self.post.user.username} Post'
"""    
    