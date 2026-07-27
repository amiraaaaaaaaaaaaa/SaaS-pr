from typing import Any

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from customers.models import Customer

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Create Customer rows for users that predate the auto-creation signal. "
        "Hits the Stripe API once per user, so it supports --dry-run."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="List what would be created without calling Stripe.",
        )

    def handle(self, *args: Any, **options: Any):
        dry_run = options["dry_run"]
        missing = User.objects.filter(customer__isnull=True)

        if not missing.exists():
            self.stdout.write(self.style.SUCCESS("Every user already has a Customer."))
            return

        for user in missing:
            if dry_run:
                self.stdout.write(f"would create Customer for {user.username} <{user.email or 'no email'}>")
                continue
            customer, _ = Customer.objects.get_or_create(user=user)
            if customer.stripe_id:
                self.stdout.write(f"{user.username} -> {customer.stripe_id}")
            else:
                self.stdout.write(self.style.WARNING(f"{user.username} -> no stripe_id (missing email or Stripe error)"))

        verb = "Would create" if dry_run else "Created"
        self.stdout.write(self.style.SUCCESS(f"{verb} {missing.count()} Customer record(s)."))
