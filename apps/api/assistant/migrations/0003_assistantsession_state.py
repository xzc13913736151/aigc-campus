from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("assistant", "0002_assistantactionproposal"),
    ]

    operations = [
        migrations.AddField(
            model_name="assistantsession",
            name="state",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
