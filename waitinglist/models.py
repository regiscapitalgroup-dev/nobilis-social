from django.db import models
from django.utils import timezone


class WaitingList(models.Model):
    # screen 1
    first_name = models.CharField(max_length=100, null=False, blank=False, verbose_name="Name")
    last_name = models.CharField(max_length=150, null=False, blank=False, verbose_name="Last Name")
    phone_number = models.CharField(max_length=20, null=False, blank=False, verbose_name="Phone Number")
    email = models.CharField(max_length=25000, null=False, blank=False, verbose_name="E-mail")
    occupation = models.CharField(max_length=60, null=True, blank=True, verbose_name="Occupation")
    country = models.CharField(max_length=4, null=True, blank=True, verbose_name="Country")
    referenced = models.CharField(max_length=60, null=True, blank=True, verbose_name="Referenced")
    # screen 2
    option0 = models.BooleanField(blank=True, default=False, verbose_name="Engage in a trusted, premium ecosysten tailored to meet your needs")
    option1 = models.BooleanField(blank=True, default=False, verbose_name="Connect with a prestigious global network of ultra-high archievers, like yourself")
    option2 = models.BooleanField(blank=True, default=False, verbose_name="Building meaningful, outcome-driven relationships for personal and professional growth, with transparent motivation and win-win outcomes")
    option3 = models.BooleanField(blank=True, default=False, verbose_name="Create and lead exclusive experiences tha showcase your expertise and passions")
    option4 = models.BooleanField(blank=True, default=False, verbose_name="Participate in unique, member-led experiences curated for exclusively Nobilis members")
    option5 = models.BooleanField(blank=True, default=False, verbose_name="Gain early access to top-tier market insights for expert knowleage in AI, investment, longevity, and more")
    option6 = models.BooleanField(blank=True, default=False, verbose_name="Sharing your expertise and values in a confidential and collaborative setting")
    option7 = models.BooleanField(blank=True, default=False, verbose_name="Contributing to a lasting legacy with exceptional individual")
    option8 = models.BooleanField(blank=True, default=False, verbose_name="Network while enjoying adventures or spending quality time with family")
    option9 = models.BooleanField(blank=True, default=False, verbose_name="Ensure lasting meaningful connections")
    other_option = models.TextField(null=True, blank=True, verbose_name="Other (Please specify)")
    # screen 3
    wealth_owner = models.BooleanField(blank=True, default=False, verbose_name="Wealth Owner")
    impact_maker = models.BooleanField(blank=True, default=False, verbose_name="Impact Maker")
    executive = models.BooleanField(blank=True, default=False, verbose_name="Executive")
    governor = models.BooleanField(blank=True, default=False, verbose_name="Governor")
    link_verify = models.CharField(max_length=255, null=True, blank=True, verbose_name="Link")
    # status 
    created_at = models.DateField(auto_now_add=True, verbose_name="Created at")
    status_waiting_list = models.IntegerField(default=0, verbose_name="Status Waiting List")

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    class Meta:
        verbose_name = "Waiting List"
        verbose_name_plural = "Waiting Lists"
        ordering = ['-created_at']
