from django.urls import path
from .views import (
    BusinessProfileView,
    CategoryListCreateView,
    SupplierListCreateView,
    ProductCreateView,
    SaleCreateView,
    NotificationListView,
    MarkAllNotificationsReadView,

)

urlpatterns = [
    path("profile/", BusinessProfileView.as_view()),
    path("categories/", CategoryListCreateView.as_view()),
    path("suppliers/", SupplierListCreateView.as_view()),
    path("products/", ProductCreateView.as_view()),
    path("sales/", SaleCreateView.as_view()),
    path("notifications/", NotificationListView.as_view(),name="notifications-list"),
    path("notifications/mark-all-read/", MarkAllNotificationsReadView.as_view(), name="notifications-mark-all-read"),

]
