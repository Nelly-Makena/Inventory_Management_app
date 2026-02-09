from datetime import timedelta
from django.utils.timezone import now

def get_date_range(range_key):
    today = now()

    if range_key == "7d":
        return today - timedelta(days=7)
    if range_key == "30d":
        return today - timedelta(days=30)
    if range_key == "6m":
        return today - timedelta(days=180)
    if range_key == "1y":
        return today - timedelta(days=365)

    return today - timedelta(days=30)  # will be the default
