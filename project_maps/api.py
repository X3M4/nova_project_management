from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ProjectLocation, BigProjectLocation
from .serializers import ProjectLocationSerializer, BigProjectLocationSerializer

 # This viewset provides CRUD operations for ProjectLocation model
class ProjectLocationViewSet(viewsets.ModelViewSet):
    queryset = ProjectLocation.objects.all()
    serializer_class = ProjectLocationSerializer
    permission_classes = [IsAuthenticated]
    
class BigProjectLocationViewSet(viewsets.ModelViewSet):
    queryset = BigProjectLocation.objects.all()
    serializer_class = ProjectLocationSerializer
    permission_classes = [IsAuthenticated]
    

   