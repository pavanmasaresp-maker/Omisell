import os

from django.contrib.auth import authenticate
from django.db import transaction
from django.db.models import ProtectedError
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from tenants.models import Tenant
from . import firebase_auth
from .models import Role, User


class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        user = authenticate(username=request.data.get("username"),
                            password=request.data.get("password"))
        if not user:
            return Response({"error": "Invalid credentials"}, status=400)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})


class GoogleLoginView(APIView):
    """App Firebase se Google login karke ID token bhejti hai. Verify hone par apna API token milta hai.
    Email pehle se kisi user ka hai to wahi login hota hai; warna (signup on ho to) naya store + Owner banta hai."""
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = request.data.get("id_token")
        if not raw:
            return Response({"error": "id_token chahiye."}, status=400)
        try:
            claims = firebase_auth.verify(raw)
        except firebase_auth.NotConfigured:
            return Response({"error": "Google login abhi server par set nahi hai."}, status=503)
        except ValueError:
            return Response({"error": "Google login verify nahi ho paya. Dobara try karo."}, status=400)

        email = (claims.get("email") or "").strip().lower()
        provider = (claims.get("firebase") or {}).get("sign_in_provider")
        if not email or not claims.get("email_verified") or provider != "google.com":
            return Response({"error": "Sirf verified Google account se login ho sakta hai."}, status=400)

        allowed = [e.strip().lower() for e in os.environ.get("FIREBASE_ALLOWED_EMAILS", "").split(",") if e.strip()]
        if allowed and email not in allowed:
            return Response({"error": "Ye email abhi allowed nahi hai."}, status=403)

        user = User.objects.filter(email__iexact=email).order_by("date_joined").first()
        if user is None:
            if os.environ.get("GOOGLE_SIGNUP", "1") != "1":
                return Response({"error": "Naye account abhi band hain."}, status=403)
            user = self._create_owner(email, claims)
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key})

    @staticmethod
    def _create_owner(email, claims):
        name = (claims.get("name") or email.split("@")[0]).strip()[:100]
        with transaction.atomic():
            tenant = Tenant.objects.create(name=f"{name}'s Store"[:200])
            username = email
            if User.objects.filter(username=username).exists():
                username = f"{email}#{str(claims.get('sub', ''))[:6]}"
            user = User(username=username[:150], email=email, first_name=name[:150],
                        tenant=tenant, role=Role.OWNER)
            user.set_unusable_password()
            user.save()
        return user


class MeView(APIView):
    def get(self, request):
        u = request.user
        return Response({"id": str(u.id), "username": u.username, "email": u.email, "role": u.role,
                         "tenant": str(u.tenant_id) if u.tenant_id else None})

    def delete(self, request):
        """Account delete (Play Store ki requirement). Body: {"confirm": "DELETE"}.
        Owner delete kare to uska poora store (products, stock, orders, channels, users) hat jata hai.
        Baaki roles sirf apna login hatate hain."""
        if request.data.get("confirm") != "DELETE":
            return Response({"error": 'Delete karne ke liye confirm mein "DELETE" bhejo.'}, status=400)
        u = request.user
        try:
            with transaction.atomic():
                if u.role == Role.OWNER and u.tenant_id:
                    u.tenant.delete()  # CASCADE: is store ka sab data + users
                else:
                    u.delete()
        except ProtectedError:
            return Response({"error": "Account abhi delete nahi ho paya. Support se baat karo."}, status=409)
        return Response(status=204)
