from django.utils import timezone
from auctions.models import AuctionListing
from utils.enums.status import Status


def close_auction(auction: AuctionListing) -> AuctionListing:
    """
    Close a single auction: determine the winner (highest bidder, if any)
    and mark it as COMPLETED. Idempotent -- calling this on an
    already-completed auction is a no-op.
    """
    if auction.status != Status.ACTIVE:
        return auction

    top_bid = auction.bids.order_by("-amount", "created_at").first()
    if top_bid is not None:
        auction.winner = top_bid.bidder
        auction.current_price = top_bid.amount

    auction.status = Status.COMPLETED
    auction.save(update_fields=["status", "winner", "current_price", "updated_at"])
    return auction


def close_expired_auctions(queryset=None) -> int:
    """
    Find every ACTIVE auction whose end_time has passed and close it.
    Returns the number of auctions closed.

    Called lazily on read endpoints so the API is always consistent even
    without a running scheduler, and is also exposed as a management
    command (`close_expired_auctions`) for use with cron/Celery beat.
    """
    qs = queryset if queryset is not None else AuctionListing.objects.all()
    expired = qs.filter(status=Status.ACTIVE, end_time__lte=timezone.now())
    count = 0
    for auction in expired:
        close_auction(auction)
        count += 1
    return count


def ensure_auction_state(auction: AuctionListing) -> AuctionListing:
    """Lazily close a single auction if it has expired, then return it fresh."""
    if auction.status == Status.ACTIVE and auction.end_time <= timezone.now():
        close_auction(auction)
        auction.refresh_from_db()
    return auction
