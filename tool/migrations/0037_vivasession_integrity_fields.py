from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0036_alter_assignment_ai_feedback_visible_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="vivasession",
            name="last_heartbeat_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vivasession",
            name="last_log_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="vivasession",
            name="heartbeat_nonce",
            field=models.CharField(blank=True, max_length=64),
        ),
        migrations.AddField(
            model_name="vivasession",
            name="tamper_suspected",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="vivasession",
            name="tamper_reason",
            field=models.TextField(blank=True),
        ),
    ]
