from django.urls import path, include
from rest_framework.routers import DefaultRouter
from waitinglist.views import WaitingListView, WaitingListAdminViewSet, RejectionReasonListView, UserExistsView

router = DefaultRouter()
router.register(r'admin', WaitingListAdminViewSet, basename='waitinglist')

urlpatterns = [ 
    path('', WaitingListView.as_view(), name='waitinglist'),
    path('rejection-reasons/', RejectionReasonListView.as_view(), name='rejection-reason-list'),
    path('', include(router.urls)),
    path('exists/', UserExistsView.as_view()),
]