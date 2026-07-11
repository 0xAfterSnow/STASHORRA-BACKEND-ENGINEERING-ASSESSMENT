from rest_framework import serializers

from accounts.serializers import UserSerializer

from .models import Bid


class BidSerializer(serializers.ModelSerializer):
    bidder = UserSerializer(read_only=True)

    class Meta:
        model = Bid
        fields = ("id", "auction", "bidder", "amount", "created_at")
        read_only_fields = ("id", "auction", "bidder", "created_at")


class BidCreateSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("amount must be greater than zero.")
        return value
