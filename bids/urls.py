from django.urls import path

from .views import BidListCreateView

urlpatterns = [
    path("<int:auction_id>/bids/", BidListCreateView.as_view(), name="bid-list-create"),
]
