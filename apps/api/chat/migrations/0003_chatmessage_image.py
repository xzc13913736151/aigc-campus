from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("chat", "0002_chatthread_hidden_flags_chatmessage_withdrawn_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="chatmessage",
            name="body",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="chatmessage",
            name="image",
            field=models.ImageField(blank=True, null=True, upload_to="chat/messages/%Y/%m/%d/"),
        ),
    ]
