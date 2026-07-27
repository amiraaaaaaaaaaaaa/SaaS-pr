import importlib
import os
from unittest.mock import patch

from django.test import SimpleTestCase

import helpers.billing


def reload_billing(debug, key):
    """Re-import helpers.billing with a given DJANGO_DEBUG / Stripe key pair.

    os.environ wins over the .env file in python-decouple, so patching it here
    exercises the module-level guards.
    """
    with patch.dict(os.environ, {"DJANGO_DEBUG": debug, "STRIPE_SECRET_KEY": key}):
        return importlib.reload(helpers.billing)


class StripeKeyGuardTests(SimpleTestCase):
    def tearDown(self):
        # Leave the module holding a sane config for any later test.
        reload_billing("1", "sk_test_teardown")

    def test_live_key_in_debug_refuses_to_start(self):
        """The dangerous direction: real charges from a dev machine."""
        with self.assertRaises(ValueError):
            reload_billing("1", "sk_live_abc123")

    def test_test_key_in_production_warns_but_starts(self):
        """Regression: raising here left gunicorn unable to boot on Railway."""
        with self.assertLogs("helpers.billing", level="WARNING") as captured:
            module = reload_billing("0", "sk_test_abc123")
        self.assertIn("TEST Stripe key", "".join(captured.output))
        self.assertEqual(module.stripe.api_key, "sk_test_abc123")

    def test_matching_key_and_environment_is_silent(self):
        for debug, key in (("1", "sk_test_abc123"), ("0", "sk_live_abc123")):
            with self.subTest(debug=debug):
                module = reload_billing(debug, key)
                self.assertEqual(module.stripe.api_key, key)

    def test_empty_key_does_not_raise(self):
        """The Docker build imports this with no Stripe key set."""
        module = reload_billing("0", "")
        self.assertEqual(module.stripe.api_key, "")
