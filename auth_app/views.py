from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import get_user_model
from rest_framework.permissions import AllowAny

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
            # Verifying the  token with Google
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

            # getting or veryfying the user 
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": first_name,
                    "last_name": last_name,
                    "username": email,
                }
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
