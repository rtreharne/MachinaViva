# Manually created to resolve parallel migration branches.
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("tool", "0024_assignmentinvitation_role"),
        ("tool", "0028_assignment_self_enroll_fields"),
    ]

    operations = []
