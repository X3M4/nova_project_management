from rest_framework import serializers
from .models import ProjectLocation
from novacartografia_employee_management.models import Project

class ProjectLocationSerializer(serializers.ModelSerializer):
    project = serializers.PrimaryKeyRelatedField(queryset=Project.objects.all())

    class Meta:
        model = ProjectLocation
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at')
