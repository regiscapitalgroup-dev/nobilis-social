from django.contrib import admin
from .models import ExperienceCategory, ExperienceOptionalEnhancement, Experience


admin.site.register(ExperienceCategory)
admin.site.register(ExperienceOptionalEnhancement)
admin.site.register(Experience)

