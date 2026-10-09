from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


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


class MeView(APIView):
    def get(self, request):
        u = request.user
        return Response({"id": str(u.id), "username": u.username, "role": u.role,
                         "tenant": str(u.tenant_id) if u.tenant_id else None})
