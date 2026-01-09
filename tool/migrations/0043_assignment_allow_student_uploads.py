from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0042_merge_20260109_0740"),
    ]

    operations = [
        migrations.AddField(
            model_name="assignment",
            name="allow_student_uploads",
            field=models.BooleanField(default=True),
        ),
    ]
