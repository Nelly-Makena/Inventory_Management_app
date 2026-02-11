from rest_framework.permissions import BasePermission
from .models import BusinessUser

#fails to give permission to anyone outside admin
class IsBusinessAdmin(BasePermission):

    def has_permission(self, request, view):
        try:
            business_user = BusinessUser.objects.get(user=request.user)
            return business_user.role == "ADMIN" and business_user.is_active
        except BusinessUser.DoesNotExist:
            return False
