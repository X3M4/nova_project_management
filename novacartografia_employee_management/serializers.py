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
    class Meta:
        model = ProjectMovementLine
        fields = '__all__'
        
