from django.contrib import admin
from nsocial.models import (
    CustomUser,
    UserProfile,
    SocialMediaProfile,
    PersonalDetail,
    Club,
    ProfessionalProfile,
    WorkPosition,
    Education,
    BoardPosition,
    NonProfitInvolvement,
    Recognition,
    Expertise,
    UserVideo,
    Experience
)


@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_active')
    search_fields = ('first_name', 'last_name', 'email',)


admin.site.register(UserProfile)
admin.site.register(SocialMediaProfile)
admin.site.register(PersonalDetail)
admin.site.register(Club)
admin.site.register(ProfessionalProfile)
admin.site.register(WorkPosition)
admin.site.register(Education)
admin.site.register(BoardPosition)
admin.site.register(NonProfitInvolvement)
admin.site.register(Recognition)
admin.site.register(Expertise)
admin.site.register(UserVideo)
admin.site.register(Experience)
