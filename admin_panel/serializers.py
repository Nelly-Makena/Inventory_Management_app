from rest_framework import serializers
from .models import BusinessUser, Invitation, ActivityLog


class BusinessUserSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source="user.email")

    class Meta:
        model = BusinessUser
        fields = ["id", "email", "role", "is_active", "last_active"]


class InvitationSerializer(serializers.ModelSerializer):

    class Meta:
        model = Invitation
        fields = ["id", "email", "role", "accepted"]


class ActivitySerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source="user.email")

    class Meta:
        model = ActivityLog
        fields = ["id", "email", "action", "description", "created_at"]
