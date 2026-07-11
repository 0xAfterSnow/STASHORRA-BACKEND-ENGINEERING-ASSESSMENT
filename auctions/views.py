from django.shortcuts import get_object_or_404
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.permissions import IsOwnerOrAdmin
from utils.enums.status import Status

from .models import AuctionListing
from .serializers import (
    AuctionListingCreateSerializer,
    AuctionListingSerializer,
    AuctionListingUpdateSerializer,
)
from .services import close_expired_auctions, ensure_auction_state


class AuctionListCreateView(APIView):
    """
    GET  /api/auctions/       -> list all auction listings (any visitor)
    POST /api/auctions/       -> create a new auction listing (authenticated)
    """

    permission_classes = [IsAuthenticatedOrReadOnly]

    @extend_schema(
        responses=AuctionListingSerializer(many=True),
        parameters=[
            OpenApiParameter("status", str, description="Filter by status: active, completed, cancelled"),
            OpenApiParameter("owner", int, description="Filter by owner user id"),
        ],
        tags=["Auctions"],
    )
    def get(self, request):
        # Lazily close anything that has expired before we report on it.
        close_expired_auctions()

        queryset = AuctionListing.objects.select_related("owner", "winner").all()

        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        owner_filter = request.query_params.get("owner")
        if owner_filter:
            queryset = queryset.filter(owner_id=owner_filter)

        serializer = AuctionListingSerializer(queryset, many=True)
        return Response(serializer.data)

    @extend_schema(request=AuctionListingCreateSerializer, responses=AuctionListingSerializer, tags=["Auctions"])
    def post(self, request):
        serializer = AuctionListingCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        auction = serializer.save()
        return Response(AuctionListingSerializer(auction).data, status=status.HTTP_201_CREATED)


class AuctionDetailView(APIView):
    """
    GET    /api/auctions/{id}/  -> retrieve a single auction (any visitor)
    PUT    /api/auctions/{id}/  -> full update (owner or admin only)
    PATCH  /api/auctions/{id}/  -> partial update (owner or admin only)
    DELETE /api/auctions/{id}/  -> delete (owner or admin only)
    """

    permission_classes = [IsAuthenticatedOrReadOnly, IsOwnerOrAdmin]

    def get_object(self, pk):
        auction = get_object_or_404(AuctionListing, pk=pk)
        self.check_object_permissions(self.request, auction)
        return auction

    @extend_schema(responses=AuctionListingSerializer, tags=["Auctions"])
    def get(self, request, pk):
        auction = self.get_object(pk)
        auction = ensure_auction_state(auction)
        return Response(AuctionListingSerializer(auction).data)

    @extend_schema(request=AuctionListingUpdateSerializer, responses=AuctionListingSerializer, tags=["Auctions"])
    def put(self, request, pk):
        return self._update(request, pk, partial=False)

    @extend_schema(request=AuctionListingUpdateSerializer, responses=AuctionListingSerializer, tags=["Auctions"])
    def patch(self, request, pk):
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        auction = self.get_object(pk)

        if auction.status != Status.ACTIVE:
            return Response(
                {"detail": "Only active auctions can be edited."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = AuctionListingUpdateSerializer(auction, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(AuctionListingSerializer(auction).data)

    @extend_schema(tags=["Auctions"])
    def delete(self, request, pk):
        auction = self.get_object(pk)
        auction.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
