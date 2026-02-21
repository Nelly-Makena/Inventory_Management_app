from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from .models import Business, Category, Supplier, Product, Sale, Notification, NotificationPreference
from .serializers import (
    BusinessSerializer,
    CategorySerializer,
    SupplierSerializer,
    ProductSerializer,
    SaleSerializer,
    NotificationSerializer,
    NotificationPreferenceSerializer,
)
from admin_panel.models import ActivityLog, BusinessUser
from admin_panel.utils import log_activity


def get_business(user):
    #businessuser works for every role
    try:
        return BusinessUser.objects.get(user=user).business
    except BusinessUser.DoesNotExist:
        return Business.objects.get(owner=user)


def check_and_notify(product, business):
    prefs = getattr(business, 'notification_preferences', None)
    low_stock_on = prefs.low_stock_alerts if prefs else True
    overstock_on = prefs.overstock_alerts if prefs else True

    if low_stock_on and product.quantity < product.min_stock_level:
        Notification.objects.create(
            business=business,
            product=product,
            type=Notification.LOW_STOCK,
            message=f"{product.name} is low — only {product.quantity} units left"
        )
    elif overstock_on and product.quantity > product.max_stock_level:
        Notification.objects.create(
            business=business,
            product=product,
            type=Notification.OVER_STOCK,
            message=f"{product.name} exceeds max stock with {product.quantity} units"
        )


class BusinessProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            business = Business.objects.get(owner=request.user)
            return Response(BusinessSerializer(business).data)
        except Business.DoesNotExist:
            return Response({}, status=status.HTTP_200_OK)

    def post(self, request):
        business, created = Business.objects.get_or_create(owner=request.user)
        serializer = BusinessSerializer(business, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CategoryListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        categories = Category.objects.filter(business=business)
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        business = get_business(request.user)
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        suppliers = Supplier.objects.filter(business=business)
        return Response(SupplierSerializer(suppliers, many=True).data)

    def post(self, request):
        business = get_business(request.user)
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        products = Product.objects.filter(business=business)
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        business = get_business(request.user)
        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(business=business)

        check_and_notify(product, business)

        ActivityLog.objects.create(
            business=business,
            user=request.user,
            action="Created Product",
            description=f"Added product '{product.name}'"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        business = get_business(request.user)
        return Product.objects.get(pk=pk, business=business)

    def get(self, request, pk):
        try:
            product = self.get_object(pk, request)
        except Product.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        return Response(ProductSerializer(product).data)

    def put(self, request, pk):
        try:
            product = self.get_object(pk, request)
        except Product.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        serializer = ProductSerializer(product, data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        business = get_business(request.user)
        check_and_notify(product, business)

        ActivityLog.objects.create(
            business=business,
            user=request.user,
            action="Updated Product",
            description=f"Updated product '{product.name}'"
        )
        return Response(serializer.data)

    def delete(self, request, pk):
        try:
            product = self.get_object(pk, request)
        except Product.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        name = product.name
        product.delete()

        business = get_business(request.user)
        ActivityLog.objects.create(
            business=business,
            user=request.user,
            action="Deleted Product",
            description=f"Deleted product '{name}'"
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SaleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        sales = Sale.objects.filter(
            product__business=business
        ).order_by('-created_at')
        return Response(SaleSerializer(sales, many=True).data)

    def post(self, request):
        business = get_business(request.user)
        serializer = SaleSerializer(data=request.data)
        if serializer.is_valid():
            sale = serializer.save()
            ActivityLog.objects.create(
                business=business,
                user=request.user,
                action="Recorded Sale",
                description=f"Sold {sale.quantity} unit(s) of '{sale.product.name}' at {sale.created_at.strftime('%H:%M on %d %b %Y')}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        notifications = (
            Notification.objects
            .filter(business=business)
            .order_by('-created_at')
        )
        return Response(NotificationSerializer(notifications, many=True).data)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business = get_business(request.user)
        Notification.objects.filter(
            business=business,
            is_read=False
        ).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


class MarkNotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        business = get_business(request.user)
        try:
            notification = Notification.objects.get(pk=pk, business=business)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"detail": "Marked as read."})


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = get_business(request.user)
        prefs, _ = NotificationPreference.objects.get_or_create(business=business)
        return Response(NotificationPreferenceSerializer(prefs).data)

    def post(self, request):
        business = get_business(request.user)
        prefs, _ = NotificationPreference.objects.get_or_create(business=business)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)