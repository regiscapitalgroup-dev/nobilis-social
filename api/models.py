from django.db import models

# Create your models here.
class InviteTmpToken(models.Model):
    user_email = models.EmailField(max_length=255, primary_key=True, unique=True)
    user_token = models.TextField()
    user_id = models.IntegerField(default=0)

    def __str__(self):
        return self.user_email


class CityCatalog(models.Model):
    name = models.CharField(max_length=255, verbose_name="City Name")
    country = models.CharField(max_length=255, verbose_name="Country")
    subcountry = models.CharField(max_length=255, null=True, blank=True, verbose_name="Sub Country")
    def __str__(self):
        return self.name

    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "City"
        verbose_name_plural = "Cities"
