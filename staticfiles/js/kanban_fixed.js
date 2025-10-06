document.addEventListener('DOMContentLoaded', function() {
    console.log('Kanban Fixed script loaded');
    
    // Prevenir ejecución múltiple
    if (window.kanbanInitialized) {
        console.log('Kanban already initialized, skipping');
        return;
    }
    window.kanbanInitialized = true;
    
    // Variables globales
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const loadingIndicator = document.getElementById('loading-indicator') || createLoadingIndicator();
    let isUpdating = false;
    let sortableInstances = [];
    
    // Crear indicador de carga si no existe
    function createLoadingIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'loading-indicator';
        indicator.className = 'hidden fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center';
        indicator.innerHTML = `
            <div class="bg-white p-4 rounded-lg shadow-lg">
                <div class="flex items-center">
                    <div class="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mr-3"></div>
                    <span>Updating...</span>
                </div>
            </div>
        `;
        document.body.appendChild(indicator);
        return indicator;
    }
    
    // Función para mostrar notificaciones
    function showToast(message, type = 'info') {
        const toast = document.createElement('div');
        const colors = {
            success: 'bg-green-600',
            error: 'bg-red-600',
            info: 'bg-blue-600'
        };
        
        toast.className = `fixed top-4 right-4 ${colors[type]} text-white px-4 py-2 rounded-lg shadow-lg z-50 transform transition-all duration-300`;
        toast.innerHTML = message;
        
        document.body.appendChild(toast);
        
        // Mostrar
        setTimeout(() => toast.style.transform = 'translateX(0)', 100);
        
        // Ocultar
        setTimeout(() => {
            toast.style.transform = 'translateX(100%)';
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
    
    // Función para actualizar empleado - MEJORADA para prevenir duplicados
    // Función para actualizar empleado - CORREGIDA
function updateEmployeeProject(employeeId, projectId) {
    if (isUpdating) {
        console.log('Update already in progress, skipping');
        return Promise.resolve(false);
    }
    
    isUpdating = true;
    loadingIndicator.classList.remove('hidden');
    
    console.log(`Updating employee ${employeeId} to project ${projectId}`);
    
    // Usar la URL pasada desde el template
    const url = window.UPDATE_EMPLOYEE_URL || '/update-employee-project/';
    
    return fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'X-CSRFToken': csrfToken,
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: new URLSearchParams({
            'employee_id': employeeId,
            'project_id': projectId || ''
        })
    })
    .then(response => {
        console.log('Response status:', response.status);
        console.log('Response URL:', response.url);
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        return response.json();
    })
    .then(data => {
        console.log('Server response:', data);
        
        if (data.success) {
            showToast('✅ Employee moved successfully!', 'success');
            return true;
        } else {
            throw new Error(data.error || data.message || 'Unknown error');
        }
    })
    .catch(error => {
        console.error('Error details:', error);
        showToast(`❌ Error: ${error.message}`, 'error');
        return false;
    })
    .finally(() => {
        isUpdating = false;
        loadingIndicator.classList.add('hidden');
    });
}
    
    // Función para limpiar duplicados
    function removeDuplicates() {
        const seenEmployees = new Set();
        const employeeCards = document.querySelectorAll('.employee-card[data-employee-id]');
        
        employeeCards.forEach(card => {
            const employeeId = card.getAttribute('data-employee-id');
            if (seenEmployees.has(employeeId)) {
                console.warn(`Removing duplicate card for employee ${employeeId}`);
                card.remove();
            } else {
                seenEmployees.add(employeeId);
            }
        });
    }
    
    // Inicializar SortableJS - VERSION SIMPLIFICADA Y ROBUSTA
    function initializeSortable() {
        // Limpiar instancias previas
        sortableInstances.forEach(instance => instance.destroy());
        sortableInstances = [];
        
        // Limpiar duplicados antes de inicializar
        removeDuplicates();
        
        const columns = document.querySelectorAll('.kanban-column');
        
        columns.forEach(column => {
            const projectId = column.getAttribute('data-project-id') || '';
            
            const sortable = new Sortable(column, {
                group: 'kanban-shared',
                animation: 200,
                easing: "cubic-bezier(0.25, 0.46, 0.45, 0.94)",
                delay: 0,
                
                // Configuración para prevenir duplicados
                removeOnSpill: false,
                revertOnSpill: true,
                
                // Clases visuales
                ghostClass: 'sortable-ghost',
                chosenClass: 'sortable-chosen',
                dragClass: 'sortable-drag',
                
                // Filtrar elementos que no se pueden arrastrar
                filter: function(evt, item, originalEvent) {
                    // No permitir arrastrar si ya hay una actualización en progreso
                    return isUpdating;
                },
                
                onStart: function(evt) {
                    const employeeId = evt.item.getAttribute('data-employee-id');
                    console.log(`Starting drag for employee ${employeeId}`);
                    
                    // Marcar elemento como siendo arrastrado
                    evt.item.setAttribute('data-being-dragged', 'true');
                    
                    // Resaltar zonas de destino
                    document.querySelectorAll('.kanban-column').forEach(col => {
                        if (col !== evt.from) {
                            col.classList.add('drop-zone-highlight');
                        }
                    });
                },
                
                onEnd: function(evt) {
                    const item = evt.item;
                    const employeeId = item.getAttribute('data-employee-id');
                    const fromColumn = evt.from;
                    const toColumn = evt.to;
                    const fromProjectId = fromColumn.getAttribute('data-project-id') || '';
                    const toProjectId = toColumn.getAttribute('data-project-id') || '';
                    
                    console.log(`Drag ended for employee ${employeeId}`, {
                        from: fromProjectId || 'unassigned',
                        to: toProjectId || 'unassigned',
                        moved: fromColumn !== toColumn
                    });
                    
                    // Limpiar marcas visuales
                    item.removeAttribute('data-being-dragged');
                    document.querySelectorAll('.kanban-column').forEach(col => {
                        col.classList.remove('drop-zone-highlight');
                    });
                    
                    // Solo actualizar si realmente cambió de columna
                    if (fromColumn !== toColumn) {
                        console.log(`Moving employee ${employeeId} from ${fromProjectId || 'unassigned'} to ${toProjectId || 'unassigned'}`);
                        
                        // Deshabilitar temporalmente todas las instancias de Sortable
                        sortableInstances.forEach(instance => {
                            instance.option('disabled', true);
                        });
                        
                        updateEmployeeProject(employeeId, toProjectId)
                            .then(success => {
                                if (!success) {
                                    // Revertir movimiento si falló
                                    console.log('Update failed, reverting move');
                                    fromColumn.appendChild(item);
                                }
                            })
                            .finally(() => {
                                // Rehabilitar Sortable después de un breve delay
                                setTimeout(() => {
                                    sortableInstances.forEach(instance => {
                                        instance.option('disabled', false);
                                    });
                                    
                                    // Verificar y limpiar duplicados después de la actualización
                                    setTimeout(removeDuplicates, 200);
                                }, 300);
                            });
                    }
                },
                
                onMove: function(evt) {
                    // Solo permitir si no hay actualización en progreso
                    return !isUpdating;
                }
            });
            
            sortableInstances.push(sortable);
            console.log(`Sortable initialized for column: ${projectId || 'unassigned'}`);
        });
        
        console.log(`Total sortable instances created: ${sortableInstances.length}`);
    }
    
    // Verificar disponibilidad de SortableJS e inicializar
    if (typeof Sortable !== 'undefined') {
        console.log('SortableJS available, initializing...');
        initializeSortable();
    } else {
        console.error('SortableJS not loaded!');
        showToast('❌ Drag & Drop library not loaded', 'error');
    }
    
    // Función para reinicializar si es necesario (útil para debugging)
    window.reinitializeKanban = function() {
        console.log('Reinitializing Kanban...');
        window.kanbanInitialized = false;
        initializeSortable();
        removeDuplicates();
        console.log('Kanban reinitialized');
    };
    
    // Observer para detectar cambios en el DOM
    const observer = new MutationObserver(function(mutations) {
        let shouldReinitialize = false;
        
        mutations.forEach(function(mutation) {
            mutation.addedNodes.forEach(function(node) {
                if (node.nodeType === 1 && 
                    (node.classList.contains('employee-card') || 
                     node.querySelector('.employee-card'))) {
                    shouldReinitialize = true;
                }
            });
        });
        
        if (shouldReinitialize) {
            setTimeout(removeDuplicates, 100);
        }
    });
    
    // Observar cambios en el contenedor principal
    const kanbanContainer = document.querySelector('.kanban-layout') || document.body;
    observer.observe(kanbanContainer, {
        childList: true,
        subtree: true
    });
    
    // Limpiar duplicados al cargar
    setTimeout(removeDuplicates, 500);
    
    console.log('Kanban Fixed system fully initialized');
});