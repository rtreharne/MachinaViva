from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0038_article"),
    ]

    operations = [
        migrations.AddField(
            model_name="article",
            name="subtitle",
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name="article",
            name="cover_focus_x",
            field=models.PositiveIntegerField(default=50, help_text="Horizontal focal point (0-100, left to right)."),
        ),
        migrations.AddField(
            model_name="article",
            name="cover_focus_y",
            field=models.PositiveIntegerField(default=50, help_text="Vertical focal point (0-100, top to bottom)."),
        ),
    ]
