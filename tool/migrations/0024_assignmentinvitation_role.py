# Generated manually: add role to invites
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tool', '0023_userprofile_verification_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='assignmentinvitation',
            name='role',
            field=models.CharField(choices=[('student', 'Student'), ('instructor', 'Instructor')], default='student', max_length=20),
        ),
    ]
