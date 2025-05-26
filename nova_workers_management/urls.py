"""
URL configuration for nova_workers_management project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from rest_framework.authtoken.views import obtain_auth_token
from novacartografia_employee_management.api import (
    EmployeeViewSet,
    ProjectViewSet,
    EmployeeNeededViewSet,
    ProjectMovementLineViewSet,
)
from project_maps.api import ProjectLocationViewSet
# Create a router and register our viewsets with it.
router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'employees_needed', EmployeeNeededViewSet)
router.register(r'project_movement_lines', ProjectMovementLineViewSet)
router.register(r'maps', ProjectLocationViewSet)

# Add the API URLs to the urlpatterns

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", lambda request: redirect('employee_list'), name='home'),
    path("", include('novacartografia_employee_management.urls')),
    path('accounts/', include('django.contrib.auth.urls')),  # For login, logout, etc.
    path('maps/', include('project_maps.urls')),  # Include project_maps URLs
    path('api/', include(router.urls)),  # Include API URLs
    path('api-auth/', include('rest_framework.urls')),  # For API authentication
    path('api/token/', obtain_auth_token),
]

# Add static and media URLs for development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
