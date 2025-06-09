from rest_framework import serializers
from .models import Employee, Project, EmployeeNeeded, ProjectMovementLine

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = '__all__'
        
class EmployeeNeededSerializer(serializers.ModelSerializer):
    class Meta:
        model = EmployeeNeeded
        fields = '__all__'

class ProjectMovementLineSerializer(serializers.ModelSerializer):
    project_name = serializers.CharField(source='project.name', read_only=True)
    previous_project_name = serializers.CharField(source='previous_project.name', read_only=True)

    class Meta:
        model = ProjectMovementLine
        fields = [
            'id',
            'employee',
            'project',
            'previous_project',
            'date',
            'project_name',
            'previous_project_name'
        ]

        
