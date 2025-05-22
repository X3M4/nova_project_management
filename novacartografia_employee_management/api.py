from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import Employee, Project, EmployeeNeeded, ProjectMovementLine
from .serializers import EmployeeSerializer, ProjectSerializer, EmployeeNeededSerializer, ProjectMovementLineSerializer

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [IsAuthenticated]

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    
class EmployeeNeededViewSet(viewsets.ModelViewSet):
    queryset = EmployeeNeeded.objects.all()
    serializer_class = EmployeeNeededSerializer
    permission_classes = [IsAuthenticated]

class ProjectMovementLineViewSet(viewsets.ModelViewSet):
    queryset = ProjectMovementLine.objects.all()
    serializer_class = ProjectMovementLineSerializer
    permission_classes = [IsAuthenticated]
    
# In this code, we define four viewsets for the models: Employee, Project, EmployeeNeeded, and ProjectMovementLine.
# Each viewset provides CRUD operations for the corresponding model and requires authentication to access.
# The `IsAuthenticated` permission class ensures that only authenticated users can access the API endpoints.
