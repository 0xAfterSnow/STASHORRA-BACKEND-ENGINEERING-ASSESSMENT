from django.core.management.base import BaseCommand

from auctions.services import close_expired_auctions


class Command(BaseCommand):
    help = "Close all active auctions whose end_time has passed, assigning the highest bidder as winner."

    def handle(self, *args, **options):
        count = close_expired_auctions()
        self.stdout.write(self.style.SUCCESS(f"Closed {count} expired auction(s)."))
