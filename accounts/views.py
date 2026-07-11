from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .serializers import LoginSerializer, LogoutSerializer, RegisterSerializer, UserSerializer


def _tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {"refresh": str(refresh), "access": str(refresh.access_token)}


class RegisterView(APIView):
    """Create a new user account (role is always 'user')."""

    permission_classes = [AllowAny]

    @extend_schema(request=RegisterSerializer, responses=UserSerializer, tags=["Auth"])
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"user": UserSerializer(user).data, "tokens": _tokens_for_user(user)},
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """Authenticate with username/password and receive a JWT pair."""

    permission_classes = [AllowAny]

    @extend_schema(request=LoginSerializer, tags=["Auth"])
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = authenticate(
            request,
            username=serializer.validated_data["username"],
            password=serializer.validated_data["password"],
        )
        if user is None:
            return Response(
                {"detail": "Invalid username or password."},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        return Response({"user": UserSerializer(user).data, "tokens": _tokens_for_user(user)})


class LogoutView(APIView):
    """Blacklist the given refresh token so it can no longer be used."""

    permission_classes = [IsAuthenticated]

    @extend_schema(request=LogoutSerializer, tags=["Auth"])
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            token = RefreshToken(serializer.validated_data["refresh"])
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "Invalid or already-blacklisted token."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({"detail": "Logged out successfully."}, status=status.HTTP_205_RESET_CONTENT)


class MeView(APIView):
    """Return the currently authenticated user's profile."""

    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer, tags=["Auth"])
    def get(self, request):
        return Response(UserSerializer(request.user).data)
