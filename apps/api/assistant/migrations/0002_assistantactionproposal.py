import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assistant", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="assistantmessage",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.AlterField(
            model_name="assistantsession",
            name="id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False),
        ),
        migrations.CreateModel(
            name="AssistantActionProposal",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("kind", models.CharField(max_length=80)),
                ("title", models.CharField(max_length=160)),
                ("target_page", models.CharField(blank=True, max_length=160)),
                ("payload", models.JSONField(blank=True, default=dict)),
                ("preview", models.JSONField(blank=True, default=dict)),
                ("fill_payload", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(choices=[("pending", "Pending"), ("executed", "Executed"), ("dismissed", "Dismissed"), ("expired", "Expired")], default="pending", max_length=20)),
                ("expires_at", models.DateTimeField()),
                ("executed_at", models.DateTimeField(blank=True, null=True)),
                ("result", models.JSONField(blank=True, default=dict)),
                ("message", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name="action_proposals", to="assistant.assistantmessage")),
                ("session", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="action_proposals", to="assistant.assistantsession")),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="assistant_action_proposals", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
    ]
