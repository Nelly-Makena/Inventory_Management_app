from django.urls import path
from .views import (
    BusinessProfileView,
    CategoryListCreateView,
    SupplierListCreateView,
    ProductListCreateView,
    ProductDetailView,
    SaleCreateView,
    NotificationListView,
    MarkAllNotificationsReadView,
    MarkNotificationReadView,
    NotificationPreferenceView,


)

urlpatterns = [
    path("profile/", BusinessProfileView.as_view()),
    path("categories/", CategoryListCreateView.as_view()),
    path("suppliers/", SupplierListCreateView.as_view()),
    path("products/", ProductListCreateView.as_view()),
    path("products/<int:pk>/", ProductDetailView.as_view()),  # GET + PUT + DELETE
    path("sales/", SaleCreateView.as_view()),
    path("notifications/", NotificationListView.as_view(), name="notifications-list"),
    path("notifications/mark-all-read/", MarkAllNotificationsReadView.as_view(), name="notifications-mark-all-read"),
    path("notifications/<int:pk>/read/", MarkNotificationReadView.as_view(), name="notification-mark-read"),
    path("notification-preferences/", NotificationPreferenceView.as_view()),
]
