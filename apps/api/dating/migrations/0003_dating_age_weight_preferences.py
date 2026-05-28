from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("dating", "0002_allow_decimal_heights"),
    ]

    operations = [
        migrations.AddField(
            model_name="datingprofile",
            name="age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="datingprofile",
            name="weight_kg",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="datingpreference",
            name="max_age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="datingpreference",
            name="max_weight_kg",
            field=models.FloatField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="datingpreference",
            name="min_age",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="datingpreference",
            name="min_weight_kg",
            field=models.FloatField(blank=True, null=True),
        ),
    ]
