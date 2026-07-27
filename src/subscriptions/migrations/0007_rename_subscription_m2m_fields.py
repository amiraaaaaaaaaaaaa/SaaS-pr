from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('subscriptions', '0006_alter_subscription_options'),
    ]

    operations = [
        migrations.RenameField(
            model_name='subscription',
            old_name='group',
            new_name='groups',
        ),
        migrations.RenameField(
            model_name='subscription',
            old_name='permission',
            new_name='permissions',
        ),
        # 0006 wiped these because Meta had been indented out of the model.
        migrations.AlterModelOptions(
            name='subscription',
            options={'permissions': [('advanced', 'Advances Perm'), ('pro', 'Pro Perm'), ('basic', 'Basic Perm')]},
        ),
    ]
