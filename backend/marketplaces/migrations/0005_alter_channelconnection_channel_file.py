from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplaces", "0004_channelconnection_auto_process"),
    ]

    operations = [
        migrations.AlterField(
            model_name="channelconnection",
            name="channel",
            field=models.CharField(
                choices=[
                    ("SHOPIFY", "Shopify"),
                    ("WOOCOMMERCE", "Woocommerce"),
                    ("DEMO", "Demo"),
                    ("FILE", "File"),
                ],
                max_length=20,
            ),
        ),
    ]
