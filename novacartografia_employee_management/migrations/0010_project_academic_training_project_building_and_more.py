# Generated by Django 5.2 on 2025-05-12 06:17

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("novacartografia_employee_management", "0009_project_manager"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="academic_training",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name="project",
            name="building",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="confine",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="drag",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="driver_license",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="leveling",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="mining",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="office_work",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="railway_carriage",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="railway_mounting",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="scanner",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="sixty_hours",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="static",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="project",
            name="twenty_hours",
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name="project",
            name="manager",
            field=models.CharField(
                blank=True,
                choices=[
                    ("cuesta", "Cuesta"),
                    ("javi", "Javi"),
                    ("guillermo", "Guillermo"),
                    ("miguelangel", "Miguel Ángel"),
                    ("oscar", "Óscar"),
                ],
                max_length=50,
                null=True,
            ),
        ),
    ]
