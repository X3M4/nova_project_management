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
    path('employee/<int:employee_id>/assign/<int:project_id>/', views.assign_employee_to_project, name='assign_employee_to_project'),
    path('employee/<int:employee_id>/unassign/', views.unassign_employee_from_project, name='unassign_employee_from_project'),
    
    
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
    
    # Rutas para empleados necesitados
    path('employee-needed/', views.employee_needed_list, name='employee_needed_list'),
    path('employee-needed/create/', views.employee_needed_create, name='employee_needed_create'),
    path('employee-needed/<int:pk>/update/', views.employee_needed_update, name='employee_needed_update'),
    path('employee-needed/<int:pk>/delete/', views.employee_needed_delete, name='employee_needed_delete'),
    path('employee-needed/<int:pk>/fulfill/', views.employee_needed_fulfill, name='employee_needed_fulfill'),
    path('employee-needed/create/from-project/<int:project_id>/', views.employee_needed_create_from_project, name='employee_needed_create_from_project'),
    
    # Añadir estas rutas
    path('future-assignments/', views.get_employee_locked_list, name='get_employee_locked_list'),
    path('future-assignments/create/', views.get_employee_locked_create, name='get_employee_locked_create'),
    path('future-assignments/create/<int:project_id>/', views.get_employee_locked_create, name='get_employee_locked_create_from_project'),
    path('future-assignments/<int:pk>/update/', views.get_employee_locked_update, name='get_employee_locked_update'),
    path('future-assignments/<int:pk>/fulfill/', views.get_employee_locked_fulfill, name='get_employee_locked_fulfill'),
    
    # Rutas para vacaciones de empleados
    path('employee-vacations/', views.employee_vacation_list, name='employee_vacation_list'),
    path('employee-vacations/create/', views.employee_vacation_create, name='employee_vacation_create'),
    path('employee-vacations/<int:pk>/update/', views.employee_vacation_update, name='employee_vacation_update'),
    path('employee-vacations/<int:pk>/delete/', views.employee_vacation_delete, name='employee_vacation_delete'),
]