# Generated by Django 5.2 on 2025-04-29 08:47

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("novacartografia_employee_management", "0003_alter_project_description"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="type",
            field=models.CharField(default="Internal", max_length=50),
        ),
    ]
