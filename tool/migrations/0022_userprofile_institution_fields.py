# Generated manually for institution capture
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0021_standalone_auth_invites'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='institution_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='institution_type',
            field=models.CharField(blank=True, max_length=50),
        ),
    ]
