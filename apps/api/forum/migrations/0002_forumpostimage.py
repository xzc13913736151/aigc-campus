from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        ("forum", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ForumPostImage",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(upload_to="forum/posts/%Y/%m/%d/")),
                (
                    "post",
                    models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="images", to="forum.forumpost"),
                ),
            ],
            options={
                "ordering": ["created_at"],
            },
        ),
    ]
