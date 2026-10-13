from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplaces", "0006_channelconnection_auto_publish"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelconnection",
            name="commission_pct",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=5),
        ),
        migrations.AddField(
            model_name="channelconnection",
            name="charge_per_order",
            field=models.DecimalField(decimal_places=2, default=0, max_digits=8),
        ),
    ]
