import os
import time

from django.core.management.base import BaseCommand

from marketplaces.order_import import pull_all
from marketplaces.sync import run_due


class Command(BaseCommand):
    help = "Pending sync jobs process karta hai. --once: ek baar chalake band."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **opts):
        self.stdout.write("Sync worker shuru (band karne ke liye Ctrl+C)")
        every = int(os.environ.get("ORDER_PULL_SECONDS", "300"))  # 0 = band
        last_pull = 0.0
        while True:
            if every > 0 and time.monotonic() - last_pull >= every and not opts["once"]:
                last_pull = time.monotonic()
                try:
                    n = pull_all()
                    if n:
                        self.stdout.write(f"pulled {n} new order(s)")
                except Exception as e:  # worker kabhi na gire
                    self.stdout.write(f"order pull error: {e}")
            n = run_due()
            if n:
                self.stdout.write(f"processed {n} job(s)")
            if opts["once"]:
                return
            if n == 0:
                time.sleep(3)
