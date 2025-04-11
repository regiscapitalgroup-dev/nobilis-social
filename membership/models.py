from django.db import models
from nsocial.models import CustomUser 


class MembershipPlan(models.Model):
    title = models.CharField(max_length=100, verbose_name="Title")
    color = models.CharField(max_length=20, verbose_name="Color")
    price_year = models.CharField(max_length=50, verbose_name="Annual Price")
    description = models.CharField(max_length=100, verbose_name="Description")
    price = models.CharField(max_length=50, verbose_name="Price")
    price_description = models.CharField(max_length=100, verbose_name="Price Description")
    features = models.JSONField(verbose_name="Features")
    requirements = models.JSONField(verbose_name="Requirements")

    class Meta:
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    def __str__(self):
        return self.title


class Suscription(models.Model):
    suscriber_name = models.CharField(max_length=250)
    plan = models.ForeignKey(MembershipPlan, on_delete=models.PROTECT)
    start_date = models.DateTimeField(auto_now_add=True)
    end_date = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=False)
    payment_stripe = models.CharField(max_length=250, default="")
    user = models.OneToOneField(CustomUser, max_length=10, on_delete=models.CASCADE)

    def __str__(self) -> str:
        return f'{self.suscriber_name} - {self.plan}'
