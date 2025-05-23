# Generated by Django 5.2 on 2025-05-14 09:38

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "novacartografia_employee_management",
            "0016_remove_getemployeelocked_employee_and_more",
        ),
    ]

    operations = [
        migrations.RemoveField(
            model_name="getemployeelocked",
            name="employee",
        ),
        migrations.AddField(
            model_name="getemployeelocked",
            name="employee",
            field=models.ForeignKey(
                blank=True,
                help_text="The employee to be assigned to the project",
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="future_assignment",
                to="novacartografia_employee_management.employee",
            ),
        ),
    ]
