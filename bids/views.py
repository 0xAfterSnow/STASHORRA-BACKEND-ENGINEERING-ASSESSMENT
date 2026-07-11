from django.db import IntegrityError
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from auctions.models import AuctionListing
from auctions.services import ensure_auction_state

from .models import Bid
from .serializers import BidCreateSerializer, BidSerializer
from utils.enums.status import Status


class BidListCreateView(APIView):
    """
    GET  /api/auctions/{auction_id}/bids/  -> full bid history for an auction
    POST /api/auctions/{auction_id}/bids/  -> place a new bid
    """

    def get_permissions(self):
        if self.request.method == "POST":
            return [IsAuthenticated()]
        return []

    @extend_schema(responses=BidSerializer(many=True), tags=["Bids"])
    def get(self, request, auction_id):
        auction = get_object_or_404(AuctionListing, pk=auction_id)
        ensure_auction_state(auction)
        bids = auction.bids.select_related("bidder").all()
        return Response(BidSerializer(bids, many=True).data)

    @extend_schema(request=BidCreateSerializer, responses=BidSerializer, tags=["Bids"])
    def post(self, request, auction_id):
        auction = get_object_or_404(AuctionListing, pk=auction_id)
        auction = ensure_auction_state(auction)

        serializer = BidCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data["amount"]

        # --- Business rules -------------------------------------------------
        if auction.status != Status.ACTIVE.value or auction.end_time <= timezone.now():
            return Response(
                {"detail": "This auction has ended and can no longer receive bids."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if auction.owner_id == request.user.id:
            return Response(
                {"detail": "You cannot bid on your own auction."},
                status=status.HTTP_403_FORBIDDEN,
            )

        if Bid.objects.filter(auction=auction, bidder=request.user).exists():
            return Response(
                {"detail": "You have already placed a bid on this auction."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if amount <= auction.current_price:
            return Response(
                {
                    "detail": (
                        f"Bid must be greater than the current highest bid "
                        f"({auction.current_price})."
                    )
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            bid = Bid.objects.create(auction=auction, bidder=request.user, amount=amount)
        except IntegrityError:
            return Response(
                {"detail": "You have already placed a bid on this auction."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        auction.current_price = amount
        auction.save(update_fields=["current_price", "updated_at"])

        return Response(BidSerializer(bid).data, status=status.HTTP_201_CREATED)
