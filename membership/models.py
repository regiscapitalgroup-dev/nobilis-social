from django.db import models
from django.conf import settings


class IntroductionCatalog(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    cost =models.DecimalField(decimal_places=2, max_digits=10, null=True, blank=True)
    stripe_product_id = models.CharField(max_length=100, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name_plural = "Introduction Catalog"


class IntroductionStatus(models.Model):
    status_name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.status_name

    class Meta:
        verbose_name_plural = "Introduction Status"


class Plan(models.Model):
    title = models.CharField(max_length=100, verbose_name="Title")
    color = models.CharField(max_length=20, verbose_name="Color")
    price_year = models.CharField(max_length=50, verbose_name="Annual Price")
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Price")
    shipping = models.DecimalField(max_digits=10, decimal_places=2, default=0, verbose_name="Shipping")
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


class ShippingAddress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='shipping')
    name = models.CharField(max_length=20, verbose_name="Name")
    address = models.TextField(null=True, blank=True, verbose_name="Shipping Address")
    country = models.CharField(max_length=80, null=True, blank=True, verbose_name="Country")
    city = models.CharField(max_length=150, null=True, blank=True, verbose_name="City")
    card_no = models.CharField(max_length=20, null=True, blank=True, verbose_name="Card Number")
    card_type = models.CharField(max_length=10, null=True, blank=True, verbose_name="Card Type")
    card_last_4 = models.CharField(max_length=5, null=True, blank=True, verbose_name="Card Last 4")
    same_billing_address = models.BooleanField(default=False, verbose_name="Billing Address is Same as shipping")
    billing_address = models.TextField(null=True, blank=True, verbose_name="Billing Address")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Shipping"
        verbose_name_plural = "Shippings"


class UserInvitation(models.Model):
    email = models.EmailField()
    invited_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_invitations')
    token = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    invited_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='invitations_received')

    class Meta:
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['token']),
        ]
        unique_together = ('email', 'invited_by')
        ordering = ['-created_at']

    def __str__(self):
        return f"Invitation to {self.email} by {self.invited_by_id}"


class MembershipSubscription(models.Model):
    user_profile = models.ForeignKey('nsocial.UserProfile', on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    status = models.CharField(max_length=20)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['stripe_subscription_id']),
            models.Index(fields=['status']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"Sub {self.stripe_subscription_id} ({self.status})"


class MemberIntroduction(models.Model):
    introduction_type = models.ForeignKey(IntroductionCatalog, on_delete=models.CASCADE, null=False, blank=False)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False, related_name='+')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=False, blank=False, related_name='+')
    topic = models.CharField(max_length=100, null=False, blank=False)
    message = models.TextField(null=False, blank=False)
    status = models.ForeignKey(IntroductionStatus, on_delete=models.CASCADE, null=False, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.introduction_type.title

    class Meta:
        verbose_name = "Introduction"
        verbose_name_plural = "Introductions"


class InviteeQualificationCatalog(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Invitee Qualification"
        verbose_name_plural = "Invitee Qualifications"

    def __str__(self):
        return self.name


class MemberReferral(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.CharField(max_length=30)
    invitee_qualification = models.ForeignKey(InviteeQualificationCatalog, on_delete=models.PROTECT, related_name='referrals')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='member_referrals')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Member Referral"
        verbose_name_plural = "Member Referrals"

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"
