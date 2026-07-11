from django.conf import settings
from django.db import models


class Bid(models.Model):
    """A single bid placed by a user on an auction listing. Immutable history."""

    auction = models.ForeignKey(
        "auctions.AuctionListing",
        on_delete=models.CASCADE,
        related_name="bids",
    )
    bidder = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="bids",
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-amount"]
        # Ensure only one bid per user per auction
        unique_together = ("auction", "bidder")

    def __str__(self):
        return f"{self.bidder} bid {self.amount} on {self.auction}"
