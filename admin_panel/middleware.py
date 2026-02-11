from django.utils.timezone import now
from .models import BusinessUser

#to automatically track last_active added users
class UpdateLastActiveMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if request.user.is_authenticated:
            try:
                business_user = BusinessUser.objects.get(user=request.user)
                business_user.last_active = now()
                business_user.save(update_fields=["last_active"])
            except BusinessUser.DoesNotExist:
                pass

        return self.get_response(request)
