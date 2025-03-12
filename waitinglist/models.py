from django.db import models


class WaitingList(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=False, blank=False, verbose_name="Name")
    lastname = models.CharField(max_length=150, null=False, blank=False, verbose_name="Last Name")
    phone_number = models.CharField(max_length=20, null=False, blank=False, verbose_name="Phone Number")
    email = models.CharField(max_length=25000, null=False, blank=False, verbose_name="E-mail")
    occupation = models.CharField(max_length=60, null=True, blank=True, verbose_name="Occupation")
    city = models.CharField(max_length=60, null=True, blank=True, verbose_name="City")
    referenced = models.CharField(max_length=60, null=True, blank=True, verbose_name="Referenced")
    is_active = models.BooleanField(default=False, verbose_name="Active")
