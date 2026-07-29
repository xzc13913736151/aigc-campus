from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assistant", "0003_assistantsession_state"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantmessage",
            name="presentation",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
