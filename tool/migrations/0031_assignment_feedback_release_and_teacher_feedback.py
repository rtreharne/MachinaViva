from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0030_alter_assignment_allow_early_submission"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="feedback_released_at",
            field=models.DateTimeField(blank=True, help_text="When AI feedback was released to students (for after_review mode).", null=True),
        ),
        migrations.AddField(
            model_name="vivasession",
            name="teacher_feedback_text",
            field=models.TextField(blank=True),
        ),
    ]
