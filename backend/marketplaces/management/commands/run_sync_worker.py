import time

from django.core.management.base import BaseCommand

from marketplaces.sync import run_due


class Command(BaseCommand):
    help = "Pending sync jobs process karta hai. --once: ek baar chalake band."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true")

    def handle(self, *args, **opts):
        self.stdout.write("Sync worker shuru (band karne ke liye Ctrl+C)")
        while True:
            n = run_due()
            if n:
                self.stdout.write(f"processed {n} job(s)")
            if opts["once"]:
                return
            if n == 0:
                time.sleep(3)
