# Generated manually for instructor email verification
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0022_userprofile_institution_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='verification_sent_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='verification_token',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='verified_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
