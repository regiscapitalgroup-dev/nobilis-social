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
    platform_access = models.BooleanField(default=False, verbose_name="Platform Access")
    profile_registration = models.BooleanField(default=False, verbose_name="Profile Registration")
    introduction_registration = models.BooleanField(default=False, verbose_name="Introduction Registration")
    experience_registration = models.BooleanField(default=False, verbose_name="Experience Registration")
    access_to_the_community_forum = models.BooleanField(default=False, verbose_name="Access to The Community Forum")
    access_experts_and_mentees = models.BooleanField(default=False, verbose_name="Access to The Experts & Mentees")
    access_to_forums_and_think_tanks = models.BooleanField(default=False, verbose_name="Access to The Forum & Think Tanks")
    professional_profile_creation = models.BooleanField(default=False, verbose_name="Professional Profile Creation")
    professional_experience_creation = models.BooleanField(default=False, verbose_name="Professional Experience Creation")
    early_access_to_pre_launch_experiences = models.BooleanField(default=False, verbose_name="Early Access to Pre-Launch Experiences")
    member_introduction = models.BooleanField(default=False, verbose_name="Member Introduction")
    dedicated_nobilis_contact = models.BooleanField(default=False, verbose_name="Dedicated Nobilis Contact")
    nobilis_founder_badge = models.BooleanField(default=False, verbose_name="Nobilis Founder Badge")

    requirements = models.JSONField(verbose_name="Requirements")

    class Meta:
        verbose_name = "Membership"
        verbose_name_plural = "Memberships"

    def __str__(self):
        return self.title
