from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0039_article_subtitle_focus"),
    ]

    operations = [
        migrations.AddField(
            model_name="vivasession",
            name="knowledge_flag",
            field=models.CharField(blank=True, max_length=32),
        ),
    ]
