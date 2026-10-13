from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplaces", "0007_channelconnection_fees"),
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
                    ("FLIPKART", "Flipkart"),
                    ("FILE", "File"),
                ],
                max_length=20,
            ),
        ),
    ]
