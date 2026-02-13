from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny
from django.utils.timezone import now

from business.models import Business
from admin_panel.models import BusinessUser, Invitation

User = get_user_model()


class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get("id_token")

        if not token:
            return Response(
                {"error": "ID token is required"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_CLIENT_ID
            )

            email = idinfo.get("email")
            first_name = idinfo.get("given_name", "")
            last_name = idinfo.get("family_name", "")

            if not email:
                return Response(
                    {"error": "Email not available from Google"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": email,
                }
            )

            # Update last_active
            business_user = BusinessUser.objects.filter(user=user).first()
            if business_user:
                business_user.last_active = now()
                business_user.save(update_fields=["last_active"])

            # If user does NOT yet belong to any business
            if not business_user:

                # the first step is checking the invitation
                invitation = Invitation.objects.filter(
                    email=email,
                    accepted=False
                ).first()

                if invitation:
                    # step 2 is to link the new user to the invite
                    BusinessUser.objects.create(
                        user=user,
                        business=invitation.business,
                        role=invitation.role,
                        is_active=True,
                        last_active=now()
                    )

                    invitation.accepted = True
                    invitation.save()

                else:
                    # if theres no invite it means its a first time users they can create a business

                    business = Business.objects.create(
                        owner=user,
                        name=f"{first_name}'s Business",
                        phone_number="",
                        address=""
                    )

                    BusinessUser.objects.create(
                        user=user,
                        business=business,
                        role="ADMIN",
                        is_active=True,
                        last_active=now()
                    )

            return Response(
                {
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "first_name": user.first_name,
                        "last_name": user.last_name,
                        "created": created,
                    }
                },
                status=status.HTTP_200_OK
            )

        except ValueError:
            return Response(
                {"error": "Invalid Google token"},
                status=status.HTTP_401_UNAUTHORIZED
            )
