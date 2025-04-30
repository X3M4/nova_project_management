from django.urls import path
from . import views

urlpatterns = [
    # Employee views
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/add/', views.employee_create, name='employee_create'),
    path('employees/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:pk>/edit/', views.employee_update, name='employee_update'),
    path('employees/<int:pk>/delete/', views.employee_delete, name='employee_delete'),
    path('employees/import/', views.import_employees_csv, name='import_employees_csv'),
    path('employees/export/', views.export_employees_csv, name='export_employees_csv'),
    
    # Project views (you'll need to implement these)
    path('projects/', views.project_list, name='project_list'),
    path('projects/add/', views.project_create, name='project_create'),
    path('projects/<int:pk>/', views.project_detail, name='project_detail'),
    path('projects/<int:pk>/edit/', views.project_update, name='project_update'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    path('projects/import/', views.import_projects_csv, name='import_projects_csv'),
    path('projects/export/', views.export_projects_csv, name='export_projects_csv'),
    
    path('movements/', views.movement_list, name='movement_list'),
    path('kanban/', views.kanban_board, name='kanban_board'),
    path('api/update-employee-project/', views.update_employee_project, name='update_employee_project'),
]