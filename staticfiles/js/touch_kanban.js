document.addEventListener('DOMContentLoaded', function() {
    // Constantes y variables necesarias del kanban original
    const columns = document.querySelectorAll('.kanban-column');
    const projectColumns = document.querySelectorAll('.project-column');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const toastNotification = document.getElementById('toast-notification');
    const toggleSidebarBtn = document.querySelector('.toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    
    // Verificar si estamos en un dispositivo táctil
    const isTouchDevice = ('ontouchstart' in window) || 
                          (navigator.maxTouchPoints > 0) || 
                          (navigator.msMaxTouchPoints > 0);
    
    console.log('Touch device detected:', isTouchDevice);
    
    // Toggle sidebar en dispositivos móviles
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
    
    // Función para mostrar notificaciones toast
    function showToast(message, type) {
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
        
        toastNotification.className = `fixed bottom-4 right-4 p-3 rounded-md shadow-lg ${bgColor} ${textColor} transform transition-all duration-300 z-50 text-sm`;
        toastNotification.innerHTML = message;
        
        setTimeout(() => {
            toastNotification.classList.remove('translate-y-full', 'opacity-0');
        }, 10);
        
        setTimeout(() => {
            toastNotification.classList.add('translate-y-full', 'opacity-0');
        }, 3000);
    }
    
    // Función para actualizar la asignación de un empleado
    function updateEmployeeProject(employeeId, projectId) {
        // Mostrar indicador de carga
        loadingIndicator.classList.remove('hidden');
        
        // Actualizar mediante AJAX
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
            
            if (data.success) {
                showToast('<i class="fas fa-check-circle mr-2"></i> Employee moved successfully!', 'success');
            } else {
                showToast(`<i class="fas fa-exclamation-triangle mr-2"></i> ${data.error || 'An error occurred'}`, 'error');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.classList.add('hidden');
            showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Network error occurred', 'error');
        });
    }

    // Habilitar SortableJS en cada columna - tanto en columnas de proyecto como en la columna de no asignados
    const sortableColumns = [];
    
    // Para cada columna kanban, inicializar Sortable
    columns.forEach(column => {
        const projectId = column.getAttribute('data-project-id');
        
        // Crear una instancia Sortable en esta columna
        const sortable = new Sortable(column, {
            group: 'employees',           // Nombre del grupo para permitir mover entre listas
            animation: 150,              // Duración de la animación en ms
            easing: "cubic-bezier(1, 0, 0, 1)", // Curva de animación más suave
            handle: '.employee-card',     // El elemento que sirve como mango para arrastrar
            draggable: '.employee-card',  // Elementos arrastrables dentro del contenedor
            ghostClass: 'dragging',       // Clase para el elemento que está siendo arrastrado
            chosenClass: 'chosen',        // Clase para el elemento seleccionado
            dragClass: 'drag',            // Clase para el elemento durante el arrastre
            forceFallback: true,          // Forzar el uso del fallback para mejor soporte táctil
            fallbackTolerance: 5,         // Tolerancia en píxeles antes de iniciar el arrastre
            touchStartThreshold: 3,       // Umbral de movimiento para iniciar arrastre táctil
            
            // Función que se ejecuta cuando se suelta un elemento
            onEnd: function(evt) {
                const employeeCard = evt.item;
                const employeeId = employeeCard.getAttribute('data-employee-id');
                const newColumn = evt.to;
                const newProjectId = newColumn.getAttribute('data-project-id');
                
                console.log(`Movido empleado ${employeeId} al proyecto ${newProjectId}`);
                
                // Actualizar en el servidor
                updateEmployeeProject(employeeId, newProjectId);
                
                // Limpiar estilos de arrastre
                setTimeout(() => {
                    document.querySelectorAll('.employee-card').forEach(card => {
                        card.classList.remove('dragging', 'chosen', 'drag');
                    });
                    document.querySelectorAll('.kanban-column').forEach(col => {
                        col.classList.remove('drop-hover');
                    });
                    document.querySelectorAll('.project-column').forEach(col => {
                        col.classList.remove('drop-hover', 'potential-drop-area');
                    });
                }, 100);
            },
            
            // Funciones para efectos visuales durante el arrastre
            onStart: function(evt) {
                const item = evt.item;
                item.classList.add('dragging');
                
                // Marcar todas las columnas como potenciales áreas de destino
                document.querySelectorAll('.project-column').forEach(col => {
                    col.classList.add('potential-drop-area');
                });
                
                console.log('Drag started for employee:', item.getAttribute('data-employee-id'));
            },
            
            onChoose: function(evt) {
                evt.item.classList.add('chosen');
            },
            
            // Indicadores visuales al arrastrar sobre una columna
            onMove: function(evt) {
                const targetColumn = evt.to;
                if (targetColumn) {
                    // Resaltar la columna destino
                    document.querySelectorAll('.kanban-column').forEach(col => {
                        col.classList.remove('drop-hover');
                    });
                    targetColumn.classList.add('drop-hover');
                }
                return true;
            }
        });
        
        sortableColumns.push(sortable);
        console.log(`SortableJS inicializado en columna con ID ${projectId || 'unassigned'}`);
    });
    
    // Para mejorar la experiencia en pantallas táctiles:
    if (isTouchDevice) {
        // Agregar clases específicas para táctil
        document.body.classList.add('touch-device');
        
        // Mensaje para usuarios táctiles la primera vez
        if (!localStorage.getItem('touch-kanban-instruction-shown')) {
            showToast('<i class="fas fa-hand-pointer mr-2"></i> Para mover empleados, mantén presionado y arrastra la tarjeta', 'info');
            localStorage.setItem('touch-kanban-instruction-shown', 'true');
        }
        
        // Crear un botón flotante de ayuda
        const helpButton = document.createElement('button');
        helpButton.innerHTML = '<i class="fas fa-question-circle"></i>';
        helpButton.className = 'fixed bottom-4 left-4 bg-blue-600 text-white rounded-full w-10 h-10 flex items-center justify-center shadow-lg z-50';
        helpButton.addEventListener('click', function() {
            showToast('<i class="fas fa-hand-pointer mr-2"></i> Para mover empleados, mantén presionado y arrastra la tarjeta', 'info');
        });
        document.body.appendChild(helpButton);
    }
    
    console.log('Touch-compatible Kanban initialized');
});