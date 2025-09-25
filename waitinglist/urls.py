from django.urls import path
from waitinglist.views import WaitingListDetailView, WaitingListInviteView, WaitingListView, UserExistsView

urlpatterns = [ 
    path('', WaitingListView.as_view(), name='waitinglist'),
    path('<int:pk>/', WaitingListDetailView.as_view()),
    path('invite/<int:pk>/', WaitingListInviteView.as_view()),
    path('exists/', UserExistsView.as_view()),
]