import logging

import stripe
from decouple import config

logger = logging.getLogger(__name__)

DJANGO_DEBUG = config("DJANGO_DEBUG", default = False, cast = bool)
STRIPE_SECRET_KEY = config("STRIPE_SECRET_KEY", default = "", cast = str)

# A live key on a dev machine can move real money, so refuse to start.
if "sk_live" in STRIPE_SECRET_KEY and DJANGO_DEBUG:
    raise ValueError(
        "Refusing to start: a LIVE Stripe key is configured with DJANGO_DEBUG=1. "
        "Use an sk_test key for local development."
    )

# A test key in production is wrong but harmless -- billing simply isn't real.
# Warn loudly instead of raising, which used to take the whole site down at
# import time and left gunicorn unable to boot.
if "sk_test" in STRIPE_SECRET_KEY and not DJANGO_DEBUG:
    logger.warning(
        "Running with DJANGO_DEBUG=0 but a TEST Stripe key -- payments are not real. "
        "Set a live key before taking real customers."
    )


stripe.api_key = STRIPE_SECRET_KEY
def create_customer(name="",
                    email="",
                    metadata=None,
                    raw=False):
    response = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata or {},
    )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id


def create_product(name="",
                    metadata=None,
                    raw=False):
    response = stripe.Product.create(
        name=name,
        metadata=metadata or {},
    )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id


def create_price(
                currency = "usd",
                unit_amount = 9999,
                interval = "month",
                product = None,
                metadata = None,
                raw=False):
    if product is None:
        return None
    response =  stripe.Price.create(
                currency = currency,
                unit_amount = unit_amount,
                recurring = {"interval" : interval},
                product = product,
                metadata = metadata or {},
            )
    if raw:
        return response
    stripe_id = response.id
    return stripe_id
