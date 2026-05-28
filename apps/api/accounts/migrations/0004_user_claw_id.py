import secrets

from django.db import migrations, models


def generate_claw_id() -> str:
    return f"CC{secrets.token_hex(3).upper()}"


def fill_claw_ids(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    used = set(User.objects.exclude(claw_id="").values_list("claw_id", flat=True))
    for user in User.objects.filter(claw_id=""):
        while True:
            candidate = generate_claw_id()
            if candidate not in used:
                used.add(candidate)
                user.claw_id = candidate
                user.save(update_fields=["claw_id"])
                break


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0003_user_wechat_openid"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="claw_id",
            field=models.CharField(blank=True, max_length=12),
        ),
        migrations.RunPython(fill_claw_ids, migrations.RunPython.noop),
        migrations.AlterField(
            model_name="user",
            name="claw_id",
            field=models.CharField(blank=True, max_length=12, unique=True),
        ),
    ]
