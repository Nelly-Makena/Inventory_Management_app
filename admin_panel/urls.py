from django.urls import path
from .views import (
    AdminDashboardView,
    UserListView,
    InviteUserView,
    DeactivateUserView,
    ActivityListView
)

urlpatterns = [
    path("dashboard/", AdminDashboardView.as_view()),
    path("users/", UserListView.as_view()),
    path("invite/", InviteUserView.as_view()),
    path("users/<int:pk>/deactivate/", DeactivateUserView.as_view()),
    path("activities/", ActivityListView.as_view()),
]
