# experiences/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ExperienceViewSet, BookingViewSet

router = DefaultRouter()
router.register('', ExperienceViewSet, basename='experience')
router.register(r'bookings', BookingViewSet, basename='booking')

urlpatterns = [
    path('', include(router.urls)),
]