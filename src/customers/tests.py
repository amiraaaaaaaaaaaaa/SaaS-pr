from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Customer

User = get_user_model()


class CustomerCreationTests(TestCase):
    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_customer_created_for_new_user(self, mock_create):
        user = User.objects.create_user("alice", email="alice@example.com")

        customer = Customer.objects.get(user=user)
        self.assertEqual(customer.stripe_id, "cus_test123")
        mock_create.assert_called_once_with(email="alice@example.com", raw=False)

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_no_stripe_call_without_an_email(self, mock_create):
        user = User.objects.create_user("bob")

        self.assertIsNone(Customer.objects.get(user=user).stripe_id)
        mock_create.assert_not_called()

    @patch("helpers.billing.create_customer", side_effect=RuntimeError("stripe is down"))
    def test_stripe_failure_does_not_break_user_creation(self, mock_create):
        """A Stripe outage must not take down signup."""
        with self.assertLogs("customers.models", level="ERROR"):
            user = User.objects.create_user("carol", email="carol@example.com")

        self.assertTrue(User.objects.filter(pk=user.pk).exists())
        self.assertIsNone(Customer.objects.get(user=user).stripe_id)

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_stripe_not_called_again_on_later_saves(self, mock_create):
        user = User.objects.create_user("dave", email="dave@example.com")
        customer = Customer.objects.get(user=user)

        customer.save()
        customer.save()

        self.assertEqual(mock_create.call_count, 1)

    @patch("helpers.billing.create_customer", return_value="cus_test123")
    def test_str(self, mock_create):
        user = User.objects.create_user("erin", email="erin@example.com")
        self.assertEqual(str(Customer.objects.get(user=user)), "erin")
