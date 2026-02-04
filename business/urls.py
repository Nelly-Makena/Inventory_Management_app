from django.urls import path
from .views import (
    BusinessProfileView,
    CategoryListCreateView,
    SupplierListCreateView,
    ProductCreateView,
)

urlpatterns = [
    path("profile/", BusinessProfileView.as_view()),
    path("categories/", CategoryListCreateView.as_view()),
    path("suppliers/", SupplierListCreateView.as_view()),
    path("products/", ProductCreateView.as_view()),
]
