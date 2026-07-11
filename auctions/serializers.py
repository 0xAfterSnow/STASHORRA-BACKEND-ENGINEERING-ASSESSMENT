from django.utils import timezone
from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import AuctionListing


class AuctionListingSerializer(serializers.ModelSerializer):
    owner = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)

    class Meta:
        model = AuctionListing
        fields = (
            "id",
            "owner",
            "title",
            "description",
            "starting_price",
            "current_price",
            "end_time",
            "status",
            "winner",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("current_price", "status", "winner", "created_at", "updated_at")

    def validate_end_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("end_time must be in the future.")
        return value

    def validate_starting_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("starting_price must be greater than zero.")
        return value


class AuctionListingCreateSerializer(AuctionListingSerializer):
    """
    Used only for creation. `current_price` is seeded from
    `starting_price` and isn't accepted from the client.
    """

    def create(self, validated_data):
        validated_data["current_price"] = validated_data["starting_price"]
        validated_data["owner"] = self.context["request"].user
        return super().create(validated_data)


class AuctionListingUpdateSerializer(serializers.ModelSerializer):
    """
    Used for PATCH/PUT. Deliberately excludes current_price/status/winner
    -- those are only ever changed by the bidding/completion business
    logic, never directly by a client.
    """

    class Meta:
        model = AuctionListing
        fields = ("title", "description", "starting_price", "end_time")

    def validate_end_time(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError("end_time must be in the future.")
        return value
