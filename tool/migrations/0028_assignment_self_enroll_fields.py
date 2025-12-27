from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("tool", "0027_assignment_allow_early_submission"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="self_enroll_token",
            field=models.CharField(blank=True, max_length=64, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="assignment",
            name="self_enroll_domain",
            field=models.CharField(blank=True, default="", max_length=255),
        ),
    ]
