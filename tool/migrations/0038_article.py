from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0037_vivasession_integrity_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="Article",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                ("slug", models.SlugField(unique=True)),
                ("summary", models.TextField(blank=True)),
                ("body", models.TextField()),
                ("cover_image", models.ImageField(blank=True, null=True, upload_to="article_covers/")),
                ("author_name", models.CharField(blank=True, max_length=120)),
                ("is_published", models.BooleanField(default=False)),
                ("published_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["-published_at", "-created_at"],
            },
        ),
    ]
