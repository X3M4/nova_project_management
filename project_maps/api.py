from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .models import ProjectLocation
from .serializers import ProjectLocationSerializer

 # This viewset provides CRUD operations for ProjectLocation model
class ProjectLocationViewSet(viewsets.ModelViewSet):
    queryset = ProjectLocation.objects.all()
    serializer_class = ProjectLocationSerializer
    permission_classes = [IsAuthenticated]
   