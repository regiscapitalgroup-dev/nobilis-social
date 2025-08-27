from django.contrib import admin
from nsocial.models import CustomUser, UserProfile, SocialMediaProfile
# Register your models here.


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active')
    search_fields = ('first_name', 'last_name', 'email',)


admin.site.register(UserProfile)
admin.site.register(SocialMediaProfile)
