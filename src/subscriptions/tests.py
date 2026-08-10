from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management import call_command
from django.test import TestCase

from .models import Subscription, UserSubs

User = get_user_model()


def sub_permissions(*codenames):
    return Permission.objects.filter(
        content_type__app_label="subscriptions", codename__in=codenames
    )


class StripeMockedTestCase(TestCase):
    """Subscription.save() creates a Stripe product, so every test that saves
    one must be mocked -- otherwise the suite spams the real Stripe account."""

    def setUp(self):
        patcher = patch("helpers.billing.create_product", return_value="prod_test123")
        self.mock_create_product = patcher.start()
        self.addCleanup(patcher.stop)
        super().setUp()


class SubscriptionModelTests(StripeMockedTestCase):
    def test_custom_permissions_exist(self):
        """Meta.permissions was once indented out of the model, which made
        migration 0006 delete these. Guard against that happening again."""
        codenames = set(
            sub_permissions("advanced", "pro", "basic").values_list("codename", flat=True)
        )
        self.assertEqual(codenames, {"advanced", "pro", "basic"})

    def test_limit_choices_to_matches_custom_permissions(self):
        field = Subscription._meta.get_field("permissions")
        qs = Permission.objects.filter(**field.get_limit_choices_to())
        self.assertEqual(qs.count(), 3)

    def test_str(self):
        self.assertEqual(str(Subscription.objects.create(name="Pro Plan")), "Pro Plan")


class SyncSubsCommandTests(StripeMockedTestCase):
    def test_pushes_subscription_permissions_onto_groups(self):
        group = Group.objects.create(name="pro-group")
        sub = Subscription.objects.create(name="Pro Plan")
        sub.groups.add(group)
        sub.permissions.set(sub_permissions("pro", "basic"))

        call_command("sync_subs")

        self.assertEqual(
            set(group.permissions.values_list("codename", flat=True)), {"pro", "basic"}
        )

    def test_skips_inactive_subscriptions(self):
        group = Group.objects.create(name="stale-group")
        group.permissions.set(sub_permissions("pro"))
        sub = Subscription.objects.create(name="Old Plan", active=False)
        sub.groups.add(group)
        sub.permissions.set(sub_permissions("basic"))

        call_command("sync_subs")

        self.assertEqual(
            set(group.permissions.values_list("codename", flat=True)), {"pro"}
        )


class UserSubsSignalTests(StripeMockedTestCase):
    def setUp(self):
        super().setUp()  # starts the Stripe mock before anything is created
        self.user = User.objects.create_user("alice", email="alice@example.com")
        self.pro_group = Group.objects.create(name="pro-group")
        self.sub = Subscription.objects.create(name="Pro Plan")
        self.sub.groups.add(self.pro_group)

    def user_group_names(self):
        return set(self.user.groups.values_list("name", flat=True))

    def test_assigns_subscription_groups(self):
        UserSubs.objects.create(user=self.user, subscription=self.sub)
        self.assertEqual(self.user_group_names(), {"pro-group"})

    def test_keeps_manually_assigned_groups(self):
        self.user.groups.add(Group.objects.create(name="hand-picked"))
        UserSubs.objects.create(user=self.user, subscription=self.sub)
        self.assertEqual(self.user_group_names(), {"pro-group", "hand-picked"})

    def test_null_subscription_drops_managed_groups_only(self):
        self.user.groups.add(Group.objects.create(name="hand-picked"))
        user_sub = UserSubs.objects.create(user=self.user, subscription=self.sub)

        user_sub.subscription = None
        user_sub.save()

        self.assertEqual(self.user_group_names(), {"hand-picked"})

    def test_switching_plans_drops_the_old_plans_group(self):
        basic_group = Group.objects.create(name="basic-group")
        basic_sub = Subscription.objects.create(name="Basic Plan")
        basic_sub.groups.add(basic_group)

        user_sub = UserSubs.objects.create(user=self.user, subscription=basic_sub)
        self.assertEqual(self.user_group_names(), {"basic-group"})

        user_sub.subscription = self.sub
        user_sub.save()
        self.assertEqual(self.user_group_names(), {"pro-group"})
