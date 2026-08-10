import logging

from django.db import models
from django.conf import settings
from allauth.account.signals import (user_signed_up as allauth_user_signed_up,
                                     email_confirmed as allauth_email_confirmed)

import helpers.billing

User = settings.AUTH_USER_MODEL

logger = logging.getLogger(__name__)


class Customer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    stripe_id = models.CharField(max_length=120, null = True,
                                 blank=True)
    init_email = models.EmailField(blank=True, null=True)
    init_email_confirmed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}"

    def save(self, *args, **kwargs):
        # Only bill against an address the user has actually proven they own.
        if not self.stripe_id and self.init_email_confirmed and self.init_email:
            # Never let a Stripe outage take down a user save -- the record
            # is written without a stripe_id and can be backfilled later.
            try:
                self.stripe_id = helpers.billing.create_customer(
                    email=self.init_email,
                    metadata={"user_id": self.user.id,
                              "username": self.user.username,
                              },
                    raw=False,
                )
            except Exception:
                logger.exception("Stripe customer creation failed for user %s", self.user_id)
        super().save(*args,**kwargs)



def allauth_user_signed_up_handler(request, user, *args, **kwargs):
    """Signup creates the Customer, but without a Stripe id yet -- the email is
    still unconfirmed at this point."""
    Customer.objects.get_or_create(
        user=user,
        defaults={"init_email": user.email, "init_email_confirmed": False},
    )


def allauth_email_confirmed_handler(request, email_address, *args, **kwargs):
    """Confirming the address is what triggers Stripe customer creation, via
    Customer.save()."""
    qs = Customer.objects.filter(
        init_email=email_address.email,
        init_email_confirmed=False,
    )
    for obj in qs:
        obj.init_email_confirmed = True
        obj.save()


allauth_user_signed_up.connect(allauth_user_signed_up_handler)
allauth_email_confirmed.connect(allauth_email_confirmed_handler)
