# Generated by Django 4.2.5 on 2024-04-06 11:21

from django.conf import settings
from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("lzr_dfinityapi", "0003_logs_amount"),
    ]

    operations = [
        migrations.RenameModel(
            old_name="Holders",
            new_name="Holder",
        ),
        migrations.RenameModel(
            old_name="Logs",
            new_name="Log",
        ),
    ]