from django.contrib import admin

from .models import AuctionListing


@admin.register(AuctionListing)
class AuctionListingAdmin(admin.ModelAdmin):
    list_display = ("title", "owner", "current_price", "status", "end_time")
    list_filter = ("status",)
    search_fields = ("title", "owner__username")
