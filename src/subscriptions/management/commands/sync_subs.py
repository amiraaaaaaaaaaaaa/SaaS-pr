from django.core.management.base import BaseCommand
from typing import Any
from subscriptions.models import Subscription


class Command(BaseCommand):
    help = "Push each active subscription's permissions onto its groups."

    def handle(self, *args: Any, **options: Any):
        qs = Subscription.objects.filter(active=True)
        for obj in qs:
            sub_perms = obj.permissions.all()
            for group in obj.groups.all():
                group.permissions.set(sub_perms)
                self.stdout.write(f"{obj.name}: {sub_perms.count()} perm(s) -> group '{group.name}'")
        self.stdout.write(self.style.SUCCESS(f"Synced {qs.count()} active subscription(s)."))
