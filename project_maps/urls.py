from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_map, name='project_map'),
    path('add-location/<int:project_id>/', views.add_project_location, name='add_project_location'),
    path('edit-location/<int:location_id>/', views.edit_project_location, name='edit_project_location'),
]