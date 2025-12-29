from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0034_assignment_deadline_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="userprofile",
            name="terms_accepted_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="userprofile",
            name="terms_version",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
