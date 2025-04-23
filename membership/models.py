from django.db import models
from nsocial.models import CustomUser 


class Plan(models.Model):
    title = models.CharField(max_length=100, verbose_name="Title")
    color = models.CharField(max_length=20, verbose_name="Color")
    price_year = models.CharField(max_length=50, verbose_name="Annual Price")
    description = models.CharField(max_length=100, verbose_name="Description")
    stripe_plan_id = models.CharField(max_length=255, unique=True)
    # price = models.DecimalField(max_digits=10, decimal_places=2)
    price_str = models.CharField(max_length=30, null=False, blank=True)
    interval = models.CharField(max_length=20, choices=[
        ('month', 'Monthly'),
        ('year', 'Yearly'),
    ], null=True, blank=True)    
    price_description = models.CharField(max_length=100, verbose_name="Price Description")
    features = models.JSONField(verbose_name="Features")
    requirements = models.JSONField(verbose_name="Requirements")

    class Meta:
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    def __str__(self):
        return self.title


"""class Subscription(models.Model):
    subscriber_name = models.CharField(max_length=250)
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT)
    is_active = models.BooleanField(default=False)
    payment_stripe = models.CharField(max_length=255, unique=True, null=True, blank=True)
    status = models.CharField(max_length=50, default='pending')  # active, canceled, incomplete, etc.
    user = models.OneToOneField(CustomUser, max_length=10, on_delete=models.CASCADE)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)

    def __str__(self) -> str:
        return f'{self.subscriber_name} - {self.plan.title} ({self.status})'"""


class Credits(models.Model):
    pass
