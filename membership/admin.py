from django.contrib import admin
from membership.models import (
    Plan,
    ShippingAddress,
    MembershipSubscription,
    UserInvitation,
    IntroductionCatalog,
    IntroductionStatus,
    MemberIntroduction,
    InviteeQualificationCatalog,
    MemberReferral
)


@admin.register(MembershipSubscription)
class MembershipSubscriptionAdmin(admin.ModelAdmin):
    list_display = (
        'stripe_subscription_id', 'user_profile', 'plan', 'status',
        'cancel_at_period_end', 'is_active', 'current_period_end', 'created_at'
    )
    list_filter = ('status', 'cancel_at_period_end', 'is_active', 'plan')


# Si aún no están registrados Plan/ShippingAddress, añádelos o conserva lo que ya tienes
@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'stripe_plan_id', 'price', 'interval')
    search_fields = ('title', 'stripe_plan_id')

@admin.register(ShippingAddress)
class ShippingAddressAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'city', 'country')
    search_fields = ('user__email', 'name', 'city', 'country')


@admin.register(UserInvitation)
class UserInvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "invited_by", "created_at", "accepted_at")
    search_fields = ('email', 'invited_by__email')

admin.site.register(IntroductionCatalog)
admin.site.register(IntroductionStatus)
admin.site.register(MemberIntroduction)

@admin.register(InviteeQualificationCatalog)
class InviteeQualificationCatalogAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    search_fields = ("name", "description")

@admin.register(MemberReferral)
class MemberReferralAdmin(admin.ModelAdmin):
    list_display = ("first_name", "last_name", "email", "phone_number", "invitee_qualification", "created_by", "created_at")
    search_fields = ("first_name", "last_name", "email", "phone_number")
    list_filter = ("invitee_qualification",)
