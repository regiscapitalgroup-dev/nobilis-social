from django.urls import path, include
from rest_framework_nested import routers
from .views import TeamViewSet, TeamMembershipViewSet

# Router principal para /teams/
router = routers.SimpleRouter()
router.register(r'teams', TeamViewSet, basename='team')

# Router anidado para /teams/{team_pk}/members/
teams_router = routers.NestedSimpleRouter(router, r'teams', lookup='team')
teams_router.register(r'members', TeamMembershipViewSet, basename='team-members')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(teams_router.urls)),
]