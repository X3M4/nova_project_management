document.addEventListener('DOMContentLoaded', function() {
    // Get all employee cards
    const employeeCards = document.querySelectorAll('.employee-card');
    const columns = document.querySelectorAll('.kanban-column');
    const projectColumns = document.querySelectorAll('.project-column');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const toastNotification = document.getElementById('toast-notification');
    const toggleSidebarBtn = document.querySelector('.toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    
    // Función para limpiar todas las clases visuales de drag and drop
    function clearAllDragVisuals() {
        // Eliminar clases de arrastre de todas las tarjetas
        document.querySelectorAll('.employee-card').forEach(card => {
            card.classList.remove('dragging');
        });
        
        // Eliminar clases de hover y potencial de todas las columnas de proyecto
        projectColumns.forEach(col => {
            col.classList.remove('drop-hover', 'potential-drop-area');
            // Añadir y luego quitar clase sin transiciones para evitar animaciones persistentes
            col.classList.add('no-transitions');
            setTimeout(() => {
                col.classList.remove('no-transitions');
            }, 50);
        });
        
        // Eliminar clases de hover de todas las columnas
        columns.forEach(col => {
            col.classList.remove('drop-hover');
        });
    }
    
    // Toggle sidebar on mobile
    if (toggleSidebarBtn) {
        toggleSidebarBtn.addEventListener('click', function() {
            sidebar.classList.toggle('open');
            const icon = this.querySelector('i');
            if (sidebar.classList.contains('open')) {
                icon.classList.remove('fa-chevron-down');
                icon.classList.add('fa-chevron-up');
            } else {
                icon.classList.remove('fa-chevron-up');
                icon.classList.add('fa-chevron-down');
            }
        });
    }
    
    // Helper function to show toast notification
    function showToast(message, type) {
        // Set colors based on type
        let bgColor, textColor;
        if (type === 'success') {
            bgColor = 'bg-green-600';
            textColor = 'text-white';
        } else if (type === 'error') {
            bgColor = 'bg-red-600';
            textColor = 'text-white';
        } else {
            bgColor = 'bg-blue-600';
            textColor = 'text-white';
        }
        
        // Set content and show toast
        toastNotification.className = `fixed bottom-4 right-4 p-3 rounded-md shadow-lg ${bgColor} ${textColor} transform transition-all duration-300 z-50 text-sm`;
        toastNotification.innerHTML = message;
        
        // Animate in
        setTimeout(() => {
            toastNotification.classList.remove('translate-y-full', 'opacity-0');
        }, 10);
        
        // Animate out after delay
        setTimeout(() => {
            toastNotification.classList.add('translate-y-full', 'opacity-0');
        }, 3000);
    }
    
    // Add drag event listeners to employee cards
    employeeCards.forEach(card => {
        card.addEventListener('dragstart', function(e) {
            // Limpiar cualquier visual persistente primero
            clearAllDragVisuals();
            
            e.dataTransfer.setData('text/plain', card.getAttribute('data-employee-id'));
            card.classList.add('dragging');
            
            // Highlight all potential drop areas
            projectColumns.forEach(col => {
                col.classList.add('potential-drop-area');
            });
            
            console.log('Drag started for employee:', card.getAttribute('data-employee-id'));
        });
        
        card.addEventListener('dragend', function() {
            // Asegurar que todas las clases visuales se limpien al final
            setTimeout(clearAllDragVisuals, 100);
            console.log('Drag ended, visuals cleared');
        });
    });
    
    // Asegurar que se limpien las clases visuales cuando se cancela un arrastre
    document.addEventListener('dragend', function() {
        setTimeout(clearAllDragVisuals, 100);
    });
    
    // Hacer clic en cualquier lugar debería limpiar visuales persistentes
    document.addEventListener('click', function() {
        setTimeout(clearAllDragVisuals, 100);
    });
    
    // Make entire project column a dropzone, not just the inner kanban-column
    projectColumns.forEach(projectColumn => {
        // Find the kanban-column inside this project column
        const kanbanColumn = projectColumn.querySelector('.kanban-column');
        
        if (!kanbanColumn) {
            console.error('No kanban column found in project column');
            return;
        }
        
        // Get project ID from the kanban column
        const projectId = kanbanColumn.getAttribute('data-project-id');
        
        // Add drop events to the entire project column
        projectColumn.addEventListener('dragover', function(e) {
            e.preventDefault();
            projectColumn.classList.add('drop-hover');
        });
        
        projectColumn.addEventListener('dragleave', function(e) {
            // Solo quitar la clase si el mouse realmente salió de este elemento
            // y no entró en un hijo
            if (!projectColumn.contains(e.relatedTarget)) {
                projectColumn.classList.remove('drop-hover');
            }
        });
        
        projectColumn.addEventListener('drop', function(e) {
            e.preventDefault();
            // Limpiar clases visuales inmediatamente
            clearAllDragVisuals();
            
            const employeeId = e.dataTransfer.getData('text/plain');
            
            console.log('Drop detected - Employee ID:', employeeId, 'Project ID:', projectId);
            
            if (!employeeId) {
                console.error('No employee ID found in drop data');
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Error: Could not identify employee', 'error');
                return;
            }
            
            // Find the card
            const card = document.querySelector(`.employee-card[data-employee-id="${employeeId}"]`);
            
            if (!card) {
                console.error('Could not find employee card with ID:', employeeId);
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Error: Could not find employee card', 'error');
                return;
            }
            
            // Show loading indicator
            loadingIndicator.classList.remove('hidden');
            
            // Update via AJAX
            fetch('/api/update-employee-project/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    project_id: projectId === '' ? null : projectId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                loadingIndicator.classList.add('hidden');
                console.log('Server response:', data);
                
                if (data.success) {
                    // Move card to the actual kanban column
                    kanbanColumn.appendChild(card);
                    
                    // Remove any existing "no employees" message
                    const emptyMessage = kanbanColumn.querySelector('.text-xs.text-gray-500.italic');
                    if (emptyMessage) {
                        emptyMessage.remove();
                    }
                    
                    // Show success toast
                    showToast('<i class="fas fa-check-circle mr-2"></i> Employee moved successfully!', 'success');
                } else {
                    // Show error toast
                    showToast(`<i class="fas fa-exclamation-triangle mr-2"></i> ${data.error || 'An error occurred'}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loadingIndicator.classList.add('hidden');
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Network error occurred', 'error');
                // Asegurar que las visuales se limpien después de un error
                clearAllDragVisuals();
            });
        });
    });
    
    // Keep the original column event listeners for the unassigned column
    columns.forEach(column => {
        // Skip if this column is inside a project column (already handled above)
        if (column.closest('.project-column')) {
            return;
        }
        
        column.addEventListener('dragover', function(e) {
            e.preventDefault();
            column.classList.add('drop-hover');
        });
        
        column.addEventListener('dragleave', function(e) {
            // Solo quitar la clase si el mouse realmente salió de este elemento
            if (!column.contains(e.relatedTarget)) {
                column.classList.remove('drop-hover');
            }
        });
        
        column.addEventListener('drop', function(e) {
            e.preventDefault();
            // Limpiar clases visuales inmediatamente
            clearAllDragVisuals();
            
            const employeeId = e.dataTransfer.getData('text/plain');
            const projectId = column.getAttribute('data-project-id');
            
            console.log('Drop detected - Employee ID:', employeeId, 'Project ID:', projectId);
            
            if (!employeeId) {
                console.error('No employee ID found in drop data');
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Error: Could not identify employee', 'error');
                return;
            }
            
            // Find the card
            const card = document.querySelector(`.employee-card[data-employee-id="${employeeId}"]`);
            
            if (!card) {
                console.error('Could not find employee card with ID:', employeeId);
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Error: Could not find employee card', 'error');
                return;
            }
            
            // Show loading indicator
            loadingIndicator.classList.remove('hidden');
            
            // Update via AJAX
            fetch('/api/update-employee-project/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    employee_id: employeeId,
                    project_id: projectId === '' ? null : projectId
                })
            })
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok: ' + response.status);
                }
                return response.json();
            })
            .then(data => {
                loadingIndicator.classList.add('hidden');
                console.log('Server response:', data);
                
                if (data.success) {
                    // Move card to the column
                    column.appendChild(card);
                    
                    // Remove any existing "no employees" message
                    const emptyMessage = column.querySelector('.text-xs.text-gray-500.italic');
                    if (emptyMessage) {
                        emptyMessage.remove();
                    }
                    
                    // Show success toast
                    showToast('<i class="fas fa-check-circle mr-2"></i> Employee moved successfully!', 'success');
                } else {
                    // Show error toast
                    showToast(`<i class="fas fa-exclamation-triangle mr-2"></i> ${data.error || 'An error occurred'}`, 'error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                loadingIndicator.classList.add('hidden');
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Network error occurred', 'error');
                // Asegurar que las visuales se limpien después de un error
                clearAllDragVisuals();
            });
        });
    });
    
    // Manejar cambios de visibilidad de página para limpiar estados visuales
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            clearAllDragVisuals();
        }
    });
    
    console.log('Drag and drop initialized with ' + employeeCards.length + ' employees, ' + 
                columns.length + ' columns, and ' + projectColumns.length + ' project columns');
});