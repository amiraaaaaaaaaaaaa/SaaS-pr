from unittest.mock import patch

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed, user_signed_up
from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Customer

User = get_user_model()


class SignupTests(TestCase):
    """Signup creates the Customer, but must not touch Stripe yet -- the email
    has not been confirmed at that point."""

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_signup_creates_unconfirmed_customer_without_calling_stripe(self, mock_create):
        user = User.objects.create_user("alice", email="alice@example.com")
        user_signed_up.send(sender=User, request=None, user=user)

        customer = Customer.objects.get(user=user)
        self.assertEqual(customer.init_email, "alice@example.com")
        self.assertFalse(customer.init_email_confirmed)
        self.assertIsNone(customer.stripe_id)
        mock_create.assert_not_called()

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_signup_signal_is_idempotent(self, mock_create):
        """Regression: a second creation path raised IntegrityError on the
        OneToOne, which broke registration entirely."""
        user = User.objects.create_user("bob", email="bob@example.com")

        user_signed_up.send(sender=User, request=None, user=user)
        user_signed_up.send(sender=User, request=None, user=user)

        self.assertEqual(Customer.objects.filter(user=user).count(), 1)


class EmailConfirmedTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("carol", email="carol@example.com")
        self.customer = Customer.objects.create(
            user=self.user, init_email="carol@example.com", init_email_confirmed=False
        )
        self.address = EmailAddress.objects.create(
            user=self.user, email="carol@example.com", verified=True, primary=True
        )

    def confirm(self):
        email_confirmed.send(sender=None, request=None, email_address=self.address)

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_confirming_email_creates_the_stripe_customer(self, mock_create):
        self.confirm()

        self.customer.refresh_from_db()
        self.assertTrue(self.customer.init_email_confirmed)
        self.assertEqual(self.customer.stripe_id, "cus_test123")

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_user_id_is_sent_to_stripe_as_metadata(self, mock_create):
        self.confirm()

        mock_create.assert_called_once_with(
            email="carol@example.com",
            metadata={"user_id": self.user.pk},
            raw=False,
        )

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_confirming_twice_does_not_create_a_second_stripe_customer(self, mock_create):
        self.confirm()
        self.confirm()

        self.assertEqual(mock_create.call_count, 1)

    @patch("helpers.billing.create_customer", side_effect=RuntimeError("stripe is down"))
    def test_stripe_failure_still_records_the_confirmation(self, mock_create):
        with self.assertLogs("customers.models", level="ERROR"):
            self.confirm()

        self.customer.refresh_from_db()
        self.assertTrue(self.customer.init_email_confirmed)
        self.assertIsNone(self.customer.stripe_id)


class CustomerSaveTests(TestCase):
    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_unconfirmed_customer_never_reaches_stripe(self, mock_create):
        user = User.objects.create_user("dave", email="dave@example.com")
        Customer.objects.create(user=user, init_email=user.email, init_email_confirmed=False)
        mock_create.assert_not_called()

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_str(self, mock_create):
        user = User.objects.create_user("erin", email="erin@example.com")
        self.assertEqual(str(Customer.objects.create(user=user)), "erin")
