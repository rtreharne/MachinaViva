from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0040_vivasession_knowledge_flag"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssignmentSettingsChange",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("changed_at", models.DateTimeField(auto_now_add=True)),
                ("changes", models.JSONField(default=dict)),
                ("assignment", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="settings_changes", to="tool.assignment")),
                ("changed_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="assignment_settings_changes", to="auth.user")),
            ],
            options={
                "ordering": ["-changed_at"],
            },
        ),
    ]
