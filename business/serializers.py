from rest_framework import serializers
from .models import Business,Category,Supplier,Product,Sale,Notification

class BusinessSerializer(serializers.ModelSerializer):
    # Allow blank to allow partial profiles
    name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    address = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Business
        fields = ["id", "name", "phone_number", "address"]

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = "__all__"
        read_only_fields = ("business",)


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = "__all__"
        read_only_fields = ("business",)


class ProductSerializer(serializers.ModelSerializer):
    stock_status = serializers.ReadOnlyField()

    class Meta:
        model = Product
        fields = "__all__"
        read_only_fields = ("business",)

class SaleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sale
        fields = "__all__"
        read_only_fields = ("unit_price", "total_price", "created_at")

class NotificationSerializer(serializers.ModelSerializer):
        product_id = serializers.IntegerField(source="product.id", read_only=True)

        class Meta:
            model = Notification
            fields = [
                "id",
                "type",
                "message",
                "product_id",
                "is_read",
                "created_at",
            ]
