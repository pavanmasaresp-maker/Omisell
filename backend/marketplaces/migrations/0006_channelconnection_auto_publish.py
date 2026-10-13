from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("marketplaces", "0005_alter_channelconnection_channel_file"),
    ]

    operations = [
        migrations.AddField(
            model_name="channelconnection",
            name="auto_publish",
            field=models.BooleanField(default=False),
        ),
    ]
