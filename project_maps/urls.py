from django.urls import path
from . import views

urlpatterns = [
    path('', views.project_map, name='project_map'),
    path('add-location/<int:project_id>/', views.add_project_location, name='add_project_location'),
    path('edit-location/<int:location_id>/', views.edit_project_location, name='edit_project_location'),
    path('edit-location/<int:location_id>/', views.edit_project_location, name='edit_project_location'),
    path('employees/locations/', views.employee_locations_list, name='employee_locations_list'),
    path('employee/<int:employee_id>/location/', views.edit_employee_location, name='edit_employee_location'),
]