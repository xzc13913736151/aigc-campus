from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("chat", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="chatmessage",
            name="is_withdrawn",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="withdrawn_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="chatthread",
            name="hidden_for_user_a",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="chatthread",
            name="hidden_for_user_b",
            field=models.BooleanField(default=False),
        ),
    ]
