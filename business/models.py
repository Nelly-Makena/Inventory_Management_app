from django.db import models
from django.contrib.auth import get_user_model
from django.conf import settings

User = get_user_model()

class Business(models.Model):
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="business"
    )
    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20)
    address = models.TextField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class Category(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="categories")
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Supplier(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=150)

    def __str__(self):
        return self.name


class Product(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE, related_name="products")
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT)

    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField()
    cost_price = models.PositiveIntegerField(default=0)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_stock_level = models.PositiveIntegerField()
    max_stock_level = models.PositiveIntegerField()

    @property
    def stock_status(self):
        return "LOW" if self.quantity < self.min_stock_level else "NORMAL"

    def __str__(self):
        return self.name


class Sale(models.Model):
    product = models.ForeignKey(
        "Product",
        on_delete=models.CASCADE,
        related_name="sales"
    )
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        #auto-culc prices
        self.unit_price = self.product.unit_price
        self.total_price = self.unit_price * self.quantity
        # reduce stock
        self.product.quantity -= self.quantity
        self.product.save()

        # checking the stock to see if we send a notification or not
        if self.product.quantity < self.product.min_stock_level:
            Notification.objects.create(
                business=self.product.business,
                product=self.product,
                type=Notification.LOW_STOCK,
                message=f"{self.product.name} is critically low - only {self.product.quantity} units left"
            )

        elif self.product.quantity > self.product.max_stock_level:
            Notification.objects.create(
                business=self.product.business,
                product=self.product,
                type=Notification.OVER_STOCK,
                message=f"{self.product.name} exceeds maximum stock level"
            )

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product.name} - {self.quantity}"


class Notification(models.Model):
    LOW_STOCK = "LOW_STOCK"
    OVER_STOCK = "OVER_STOCK"

    TYPE_CHOICES = [
        (LOW_STOCK, "Low Stock"),
        (OVER_STOCK, "Over Stock"),
    ]

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="notifications"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="notifications"
    )

    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    message = models.TextField()

    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

class NotificationPreference(models.Model):
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name="notification_preferences"
    )
    low_stock_alerts  = models.BooleanField(default=True)
    overstock_alerts  = models.BooleanField(default=True)

    def __str__(self):
        return f"Prefs for {self.business.name}"