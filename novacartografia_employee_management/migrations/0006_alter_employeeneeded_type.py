# Generated by Django 5.2 on 2025-05-05 10:49

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        (
            "novacartografia_employee_management",
            "0005_alter_employee_project_id_alter_project_type_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="employeeneeded",
            name="type",
            field=models.CharField(
                choices=[
                    ("topo", "Topo"),
                    ("auxiliar", "Auxiliar"),
                    ("piloto", "Piloto"),
                ],
                default="topo",
                max_length=50,
            ),
        ),
    ]
