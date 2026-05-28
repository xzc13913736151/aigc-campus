from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dating", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="datingpreference",
            name="max_height_cm",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="datingpreference",
            name="min_height_cm",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name="datingprofile",
            name="height_cm",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
