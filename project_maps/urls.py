from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_map, name='project_map'),
    
    # URLs para BigProjectLocation
    path('big-projects/', views.big_project_list, name='big_project_list'),
    path('big-projects/create/', views.big_project_create, name='big_project_create'),
    path('big-projects/<int:pk>/', views.big_project_detail, name='big_project_detail'),
    path('big-projects/<int:pk>/edit/', views.big_project_edit, name='big_project_edit'),
    path('big-projects/<int:pk>/delete/', views.big_project_delete, name='big_project_delete'),
    
    # API endpoints
    path('api/geocode/', views.geocode_address, name='geocode_address'),
    
    # URLs existentes para ProjectLocation
    path('add-location/<int:project_id>/', views.add_project_location, name='add_project_location'),
    path('edit-location/<int:location_id>/', views.edit_project_location, name='edit_project_location'),
    path('edit-location/<int:location_id>/', views.edit_project_location, name='edit_project_location'),
    path('employees/locations/', views.employee_locations_list, name='employee_locations_list'),
    path('employee/<int:employee_id>/location/', views.edit_employee_location, name='edit_employee_location'),
]