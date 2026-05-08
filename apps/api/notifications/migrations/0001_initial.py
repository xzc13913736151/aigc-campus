from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Notification",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("forum_like", "Forum like"),
                            ("forum_comment", "Forum comment"),
                            ("forum_reply", "Forum reply"),
                            ("team_application_created", "Team application created"),
                            ("team_application_accepted", "Team application accepted"),
                            ("team_application_rejected", "Team application rejected"),
                            ("chat_message", "Chat message"),
                        ],
                        max_length=40,
                    ),
                ),
                ("title", models.CharField(max_length=120)),
                ("body", models.CharField(max_length=280)),
                ("target_type", models.CharField(blank=True, max_length=40)),
                ("target_id", models.CharField(blank=True, max_length=64)),
                ("extra", models.JSONField(blank=True, default=dict)),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sent_notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "recipient",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="notifications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "ordering": ["is_read", "-created_at"],
            },
        ),
    ]
