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
            name="ChatThread",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_type", models.CharField(blank=True, max_length=30)),
                ("source_id", models.CharField(blank=True, max_length=64)),
                (
                    "user_a",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_threads_as_a", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "user_b",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chat_threads_as_b", to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"ordering": ["-updated_at"]},
        ),
        migrations.CreateModel(
            name="ChatMessage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("body", models.TextField()),
                ("is_read", models.BooleanField(default=False)),
                ("read_at", models.DateTimeField(blank=True, null=True)),
                (
                    "sender",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="sent_chat_messages", to=settings.AUTH_USER_MODEL),
                ),
                (
                    "thread",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="messages", to="chat.chatthread"),
                ),
            ],
            options={"ordering": ["created_at"]},
        ),
        migrations.AddConstraint(
            model_name="chatthread",
            constraint=models.UniqueConstraint(fields=("user_a", "user_b"), name="unique_chat_thread_pair"),
        ),
    ]
