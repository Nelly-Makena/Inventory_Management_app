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


# checks stock and creates a notification if the business has that alert enabled
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
            serializer = BusinessSerializer(business)
            return Response(serializer.data)
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
        business = request.user.business
        categories = Category.objects.filter(business=business)
        return Response(CategorySerializer(categories, many=True).data)

    def post(self, request):
        business = request.user.business
        serializer = CategorySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SupplierListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        suppliers = Supplier.objects.filter(business=business)
        return Response(SupplierSerializer(suppliers, many=True).data)

    def post(self, request):
        business = request.user.business
        serializer = SupplierSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductListCreateView(APIView):
    # get all products and post a new one
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_user = BusinessUser.objects.get(user=request.user)
        products = Product.objects.filter(business=business_user.business)
        return Response(ProductSerializer(products, many=True).data)

    def post(self, request):
        business_user = BusinessUser.objects.get(user=request.user)
        business = business_user.business

        serializer = ProductSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save(business=business)

        check_and_notify(product, business)  # notify if stock already out of range

        ActivityLog.objects.create(
            business=business,
            user=request.user,
            action="Created Product",
            description=f"Added product '{product.name}'"
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductDetailView(APIView):
    # single product — get, update, delete
    permission_classes = [IsAuthenticated]

    def get_object(self, pk, request):
        business_user = BusinessUser.objects.get(user=request.user)
        return Product.objects.get(pk=pk, business=business_user.business)

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

        business_user = BusinessUser.objects.get(user=request.user)
        check_and_notify(product, business_user.business)  # notify if updated qty is out of range

        ActivityLog.objects.create(
            business=business_user.business,
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

        business_user = BusinessUser.objects.get(user=request.user)
        ActivityLog.objects.create(
            business=business_user.business,
            user=request.user,
            action="Deleted Product",
            description=f"Deleted product '{name}'"
        )
        return Response(status=status.HTTP_204_NO_CONTENT)


class SaleCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_user = BusinessUser.objects.get(user=request.user)
        sales = Sale.objects.filter(
            product__business=business_user.business
        ).order_by('-created_at')
        return Response(SaleSerializer(sales, many=True).data)

    def post(self, request):
        business_user = BusinessUser.objects.get(user=request.user)
        business = business_user.business

        serializer = SaleSerializer(data=request.data)
        if serializer.is_valid():
            sale = serializer.save()

            # recording the activity log
            ActivityLog.objects.create(
                business=business,
                user=request.user,
                action="Recorded Sale",
                description=f"Sold {sale.quantity} unit(s) of '{sale.product.name}' at {sale.created_at.strftime('%H:%M on %d %b %Y')}"
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# get notifications for the frontend
class NotificationListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        notifications = (
            Notification.objects
            .filter(business=business)
            .order_by('-created_at')
        )
        return Response(NotificationSerializer(notifications, many=True).data)


class MarkAllNotificationsReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        business = request.user.business
        Notification.objects.filter(
            business=business,
            is_read=False
        ).update(is_read=True)
        return Response({"detail": "All notifications marked as read."})


class MarkNotificationReadView(APIView):
    # for dismissing a single notification
    permission_classes = [IsAuthenticated]

    def patch(self, request, pk):
        business = request.user.business
        try:
            notification = Notification.objects.get(pk=pk, business=business)
        except Notification.DoesNotExist:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)

        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response({"detail": "Marked as read."})


# get and save notification preferences
class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business = request.user.business
        prefs, _ = NotificationPreference.objects.get_or_create(business=business)
        return Response(NotificationPreferenceSerializer(prefs).data)

    def post(self, request):
        business = request.user.business
        prefs, _ = NotificationPreference.objects.get_or_create(business=business)
        serializer = NotificationPreferenceSerializer(prefs, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)