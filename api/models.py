from django.db import models
from django.conf import settings


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


class LanguageCatalog(models.Model):
    name = models.CharField(max_length=255, verbose_name="Language Name")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Language"
        verbose_name_plural = "Languages"
        ordering = ['name']


class RelationshipCatalog(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name = 'Relationship'
        verbose_name_plural = 'Relationships'
        ordering = ['name']

    def __str__(self):
        return self.name


class Relative(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='relatives')
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100, blank=True, default='')
    year_of_birth = models.IntegerField(null=True, blank=True)
    relationship = models.ForeignKey('RelationshipCatalog', on_delete=models.PROTECT, related_name='relatives')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Relative'
        verbose_name_plural = 'Relatives'

    def __str__(self):
        return f"{self.first_name} {self.last_name}" if self.last_name else self.first_name


class SupportAgent(models.Model):
    name = models.CharField(max_length=255, verbose_name="Support Agent Name")
    email = models.EmailField(max_length=255, verbose_name="Support Agent Email")
    phone_number = models.CharField(max_length=255, verbose_name="Support Agent Phone Number")

    aviable_until = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Support Agent'
        verbose_name_plural = 'Support Agents'


class IndustryCatalog(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Industry'
        verbose_name_plural = 'Industries'
        ordering = ['name']


class ProfessionalInterestCatalog(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Professional Interest'
        verbose_name_plural = 'Professional Interests'
        ordering = ['name']


class HobbyCatalog(models.Model):
    name = models.CharField(max_length=255, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Hobby'
        verbose_name_plural = 'Hobbies'
        ordering = ['name']


class ClubCatalog(models.Model):
    """Catalog of clubs with name and city."""
    name = models.CharField(max_length=255, unique=True)
    city = models.CharField(max_length=255)
    active = models.BooleanField(default=True)

    def __str__(self):
        # Show as "Name - City"
        return f"{self.name} - {self.city}" if self.city else self.name

    class Meta:
        verbose_name = 'Club'
        verbose_name_plural = 'Clubs'
        ordering = ['name']


class RateExpertise(models.Model):
    """Catalog for expertise rate types (e.g., hour, project)."""
    name = models.CharField(max_length=50, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Rate Expertise'
        verbose_name_plural = 'Rate Expertise'
        ordering = ['name']
