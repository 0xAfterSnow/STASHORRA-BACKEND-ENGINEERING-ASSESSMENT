from django.urls import path

from .views import AuctionDetailView, AuctionListCreateView

urlpatterns = [
    path("", AuctionListCreateView.as_view(), name="auction-list-create"),
    path("<int:pk>/", AuctionDetailView.as_view(), name="auction-detail"),
]
