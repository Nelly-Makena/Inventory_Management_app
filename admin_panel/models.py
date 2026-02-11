from django.db import models
from django.contrib.auth import get_user_model
from business.models import Business

User = get_user_model()

#to create new users
class BusinessUser(models.Model):

    ROLE_CHOICES = (
        ("ADMIN", "Admin"),
        ("MANAGER", "Manager"),
        ("CASHIER", "Cashier"),
    )

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="members"
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    is_active = models.BooleanField(default=True)
    last_active = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.role}"

#sending an invite to the users created
class Invitation(models.Model):

    ROLE_CHOICES = (
        ("MANAGER", "Manager"),
        ("CASHIER", "Cashier"),
    )

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="invitations"
    )
    email = models.EmailField()
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    accepted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email} invited as {self.role}"

#to have activities of other users to the admin panel
class ActivityLog(models.Model):

    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name="activities"
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True
    )
    action = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action}"
