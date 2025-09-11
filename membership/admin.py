from django.contrib import admin
from membership.models import Plan, ShippingAddress, MembershipSubscription


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
