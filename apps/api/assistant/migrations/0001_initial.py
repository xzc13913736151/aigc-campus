import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="AssistantSession",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("title", models.CharField(max_length=120, blank=True)),
                ("page_type", models.CharField(choices=[("forum", "Forum"), ("publish", "Publish"), ("messages", "Messages"), ("me", "Me"), ("general", "General")], default="general", max_length=20)),
                ("context_path", models.CharField(max_length=120, blank=True)),
                ("context_target_type", models.CharField(max_length=40, blank=True)),
                ("context_target_id", models.CharField(max_length=64, blank=True)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assistant_sessions", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="AssistantMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("role", models.CharField(choices=[("user", "User"), ("assistant", "Assistant")], max_length=20)),
                ("body", models.TextField()),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="assistant.assistantsession")),
            ],
            options={"ordering": ["created_at"]},
        ),
    ]
