import logging

from django.db import models
from django.conf import settings
from django.db.models.signals import post_save

import helpers.billing

User = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null = True,
                                 blank=True)

    def __str__(self):
        return f"{self.user.username}"

    def save(self, *args, **kwargs):
        if not self.stripe_id:
            email = self.user.email
            if email:
                # Never let a Stripe outage take down a user save -- the record
                # is written without a stripe_id and can be backfilled later.
                try:
                    self.stripe_id = helpers.billing.create_customer(email=email, raw=False)
                except Exception:
                    logger.exception("Stripe customer creation failed for user %s", self.user_id)
        super().save(*args,**kwargs)


def user_did_save(sender, instance, created, *args, **kwargs):
    """Give every new user a Customer (and therefore a Stripe id)."""
    if created:
        Customer.objects.get_or_create(user=instance)


post_save.connect(user_did_save, sender=User)
