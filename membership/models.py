from django.db import models


class Plan(models.Model):
    title = models.CharField(max_length=100, verbose_name="Title")
    color = models.CharField(max_length=20, verbose_name="Color")
    price_year = models.CharField(max_length=50, verbose_name="Annual Price")
    description = models.CharField(max_length=100, verbose_name="Description")
    stripe_plan_id = models.CharField(max_length=255, unique=True)
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
