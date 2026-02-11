from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import BusinessUser, ActivityLog
from .permissions import IsBusinessAdmin

#the frontend stats
class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def get(self, request):

        business = request.user.business
#total users
        total_users = BusinessUser.objects.filter(
            business=business
        ).count()
#active users now
        active_now = BusinessUser.objects.filter(
            business=business,
            last_active__gte=now() - timedelta(minutes=10)
        ).count()
#no. of actions done today
        actions_today = ActivityLog.objects.filter(
            business=business,
            created_at__date=now().date()
        ).count()
#no. of distinct roles
        roles_count = BusinessUser.objects.filter(
            business=business
        ).values("role").distinct().count()

        return Response({
            "total_users": total_users,
            "active_now": active_now,
            "actions_today": actions_today,
            "roles": roles_count
        })

#frontend listing users
class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def get(self, request):
        business = request.user.business
        users = BusinessUser.objects.filter(business=business)
        serializer = BusinessUserSerializer(users, many=True)
        return Response(serializer.data)


#inviting user after user creation

class InviteUserView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def post(self, request):
        business = request.user.business
        serializer = InvitationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(business=business)
        return Response(serializer.data)

#deactivating users as the admin

class DeactivateUserView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def patch(self, request, pk):

        business_user = BusinessUser.objects.get(pk=pk)
        business_user.is_active = False
        business_user.save()

        return Response({"message": "User deactivated"})

#Activity lists on the admin pannel
class ActivityListView(APIView):
    permission_classes = [IsAuthenticated, IsBusinessAdmin]

    def get(self, request):
        business = request.user.business
        activities = ActivityLog.objects.filter(
            business=business
        ).order_by("-created_at")[:20]

        serializer = ActivitySerializer(activities, many=True)
        return Response(serializer.data)
