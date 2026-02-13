from .models import ActivityLog


def log_activity(business, user, action, description):
    ActivityLog.objects.create(
        business=business,
        user=user,
        action=action,
        description=description
    )



