from django.db import models
from django.contrib.auth.models import Group, Permission
from django.conf import settings
from django.db.models.signals import post_save


User = settings.AUTH_USER_MODEL
ALLOW_CUSTOM_GROUPS = True

SUBSCRIPTION_PERMISSIONS = [
            ("advanced", "Advances Perm"), #subscriptions.advanced
            ("pro", "Pro Perm"), #Pro
            ("basic", "Basic Perm") #Basic
        ]


class Subscription(models.Model):
    name = models.CharField(max_length=120)
    groups = models.ManyToManyField(Group)
    active = models.BooleanField(default=True)
    permissions = models.ManyToManyField(Permission, limit_choices_to={"content_type__app_label" : "subscriptions",
                                                                      "codename__in" :[x[0] for x in
                                                                      SUBSCRIPTION_PERMISSIONS]})

    class Meta:
        permissions = SUBSCRIPTION_PERMISSIONS

    def __str__(self):
        return f"{self.name}"


class UserSubs(models.Model):
    user = models.OneToOneField(User, on_delete = models.CASCADE)
    subscription = models.ForeignKey(Subscription, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.user} - {self.subscription}"


def user_sub_post_save(sender, instance, *args, **kwargs):
    user = instance.user
    subscription_obj = instance.subscription

    groups_ids = []
    if subscription_obj is not None:
        groups_ids = list(subscription_obj.groups.values_list("id", flat=True))

    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
        return

    # Keep any group the user was given by hand, but drop groups that belong to
    # a *different* subscription -- those are managed here, not custom.
    other_subs_qs = Subscription.objects.all()
    if subscription_obj is not None:
        other_subs_qs = other_subs_qs.exclude(id=subscription_obj.id)
    managed_elsewhere = set(other_subs_qs.values_list("groups__id", flat=True))
    managed_elsewhere.discard(None)

    current_groups = set(user.groups.values_list("id", flat=True))
    custom_groups = current_groups - managed_elsewhere
    user.groups.set(list(set(groups_ids) | custom_groups))


post_save.connect(user_sub_post_save, sender = UserSubs)
