from django.conf import settings
from django.db import models
from utils.enums.status import Status


class AuctionListing(models.Model):
    """An item put up for auction by a user."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="auctions",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    starting_price = models.DecimalField(max_digits=12, decimal_places=2)
    current_price = models.DecimalField(max_digits=12, decimal_places=2)
    end_time = models.DateTimeField()
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.ACTIVE.value)
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="won_auctions",
        null=True,
        blank=True,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.status})"
