from django.urls import path
from bases.views import HomePageView

urlpatterns = [
    path('', HomePageView.as_view(), name='home'),
]
