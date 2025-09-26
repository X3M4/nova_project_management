console.log('🚀 Cargando touch_kanban.js...');

// Esperar a que el DOM y SortableJS estén listos
function initializeDragDrop() {
    console.log('🔧 Inicializando Drag & Drop...');
    
    // Verificar que SortableJS esté disponible
    if (typeof Sortable === 'undefined') {
        console.error('❌ SortableJS no está disponible');
        return;
    }
    
    // Variables globales
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        console.error('❌ CSRF token no encontrado');
        return;
    }
    
    let sortableInstances = [];
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    
    console.log(`📱 Dispositivo táctil: ${isTouchDevice}`);
    
    // Función para mostrar notificaciones
    function showToast(message, type = 'success') {
        // Crear container si no existe
        let toastContainer = document.getElementById('toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toast-container';
            toastContainer.className = 'fixed top-4 right-4 z-50 space-y-2';
            document.body.appendChild(toastContainer);
        }
        
        const toast = document.createElement('div');
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        
        toast.className = `${bgColor} text-white px-6 py-3 rounded-lg shadow-lg transform translate-x-full transition-all duration-300 flex items-center max-w-sm`;
        toast.innerHTML = message;
        
        toastContainer.appendChild(toast);
        
        // Mostrar
        setTimeout(() => toast.classList.remove('translate-x-full'), 10);
        
        // Ocultar
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            setTimeout(() => toast.remove(), 300);
        }, 4000);
    }
    
    // Función para actualizar empleado
    function updateEmployeeProject(employeeId, projectId, employeeName) {
        console.log(`🔄 Moviendo empleado ${employeeId} al proyecto ${projectId}`);
        
        // Mostrar loading
        showToast(`<i class="fas fa-spinner fa-spin mr-2"></i>Moviendo ${employeeName}...`, 'info');
        
        fetch('/api/update-employee-project/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                employee_id: parseInt(employeeId),
                project_id: projectId ? parseInt(projectId) : null
            })
        })
        .then(response => {
            console.log(`📡 Response status: ${response.status}`);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('📥 Respuesta:', data);
            
            if (data.success) {
                const projectName = projectId ? 
                    (document.querySelector(`[data-project-id="${projectId}"] .project-title`)?.textContent || `Proyecto ${projectId}`) : 
                    'Sin asignar';
                
                showToast(`<i class="fas fa-check-circle mr-2"></i>${employeeName} → ${projectName}`, 'success');
                updateEmployeeCounters();
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            showToast(`<i class="fas fa-exclamation-triangle mr-2"></i>Error: ${error.message}`, 'error');
        });
    }
    
    // Función para actualizar contadores
    function updateEmployeeCounters() {
        document.querySelectorAll('[data-project-id]').forEach(column => {
            const employeeCards = column.querySelectorAll('.employee-card');
            const counter = column.querySelector('.employee-count');
            if (counter) {
                counter.textContent = `(${employeeCards.length})`;
            }
        });
        
        // Actualizar contador de sin asignar
        const unassignedColumn = document.querySelector('.unassigned-employees');
        if (unassignedColumn) {
            const employeeCards = unassignedColumn.querySelectorAll('.employee-card');
            const counter = document.querySelector('.sidebar .employee-count');
            if (counter) {
                counter.textContent = `(${employeeCards.length})`;
            }
        }
    }
    
    // Limpiar instancias existentes
    function cleanupSortable() {
        sortableInstances.forEach(instance => {
            if (instance && typeof instance.destroy === 'function') {
                instance.destroy();
            }
        });
        sortableInstances = [];
    }
    
    // Configurar Sortable para todas las columnas
    function setupSortable() {
        cleanupSortable();
        
        // Buscar todas las columnas que pueden recibir empleados
        const columns = [
            ...document.querySelectorAll('.kanban-column[data-project-id]'), // Columnas de proyectos
            document.querySelector('.unassigned-employees') // Columna de sin asignar
        ].filter(col => col !== null);
        
        console.log(`🎯 Configurando ${columns.length} columnas para drag & drop`);
        
        columns.forEach((column, index) => {
            const projectId = column.dataset.projectId || null;
            const isUnassigned = column.classList.contains('unassigned-employees');
            
            console.log(`📋 Columna ${index}: ${isUnassigned ? 'Sin asignar' : `Proyecto ${projectId}`}`);
            
            try {
                const sortableInstance = Sortable.create(column, {
                    group: 'kanban-employees', // Permite mover entre grupos
                    animation: 200,
                    
                    // Configuración para touch
                    touchStartThreshold: isTouchDevice ? 10 : 0,
                    delay: isTouchDevice ? 150 : 0,
                    delayOnTouchStart: true,
                    
                    // Clases CSS
                    ghostClass: 'sortable-ghost',
                    chosenClass: 'sortable-chosen', 
                    dragClass: 'sortable-drag',
                    
                    // Qué elementos se pueden arrastrar
                    draggable: '.employee-card',
                    
                    // Callbacks
                    onStart: function(evt) {
                        console.log('🎬 Inicio de drag');
                        evt.item.classList.add('is-dragging');
                        
                        // Resaltar zonas de drop
                        columns.forEach(col => {
                            if (col !== evt.from) {
                                col.classList.add('drop-zone-active');
                            }
                        });
                    },
                    
                    onMove: function(evt) {
                        // Permitir todos los movimientos
                        return true;
                    },
                    
                    onEnd: function(evt) {
                        console.log('🏁 Fin de drag');
                        
                        // Limpiar clases visuales
                        evt.item.classList.remove('is-dragging');
                        columns.forEach(col => {
                            col.classList.remove('drop-zone-active');
                        });
                        
                        // Obtener información del movimiento
                        const employeeCard = evt.item;
                        const employeeId = employeeCard.dataset.employeeId;
                        const employeeName = employeeCard.querySelector('.employee-name')?.textContent?.trim() || 'Empleado';
                        
                        const targetColumn = evt.to;
                        const sourceColumn = evt.from;
                        
                        const newProjectId = targetColumn.dataset.projectId || null;
                        const oldProjectId = sourceColumn.dataset.projectId || null;
                        
                        console.log(`📊 Movimiento:`, {
                            employeeId,
                            employeeName,
                            from: oldProjectId || 'sin asignar',
                            to: newProjectId || 'sin asignar'
                        });
                        
                        // Solo hacer la petición si cambió de columna
                        if (oldProjectId !== newProjectId) {
                            updateEmployeeProject(employeeId, newProjectId, employeeName);
                        } else {
                            console.log('ℹ️ No hay cambio de proyecto, solo reordenamiento');
                        }
                    }
                });
                
                sortableInstances.push(sortableInstance);
                console.log(`✅ Sortable configurado para columna ${index}`);
                
            } catch (error) {
                console.error(`❌ Error configurando columna ${index}:`, error);
            }
        });
        
        console.log(`🎉 ${sortableInstances.length} instancias de Sortable creadas`);
        
        // Mostrar mensaje de instrucciones
        setTimeout(() => {
            const message = isTouchDevice ? 
                '<i class="fas fa-mobile-alt mr-2"></i>Mantén presionado para arrastrar empleados' :
                '<i class="fas fa-mouse-pointer mr-2"></i>Arrastra empleados entre columnas';
            showToast(message, 'info');
        }, 1000);
    }
    
    // Observar cambios en el DOM
    const observer = new MutationObserver(function(mutations) {
        let shouldReinit = false;
        
        mutations.forEach(function(mutation) {
            if (mutation.type === 'childList') {
                mutation.addedNodes.forEach(function(node) {
                    if (node.nodeType === 1) { // Element node
                        if (node.classList?.contains('employee-card') || 
                            node.classList?.contains('kanban-column') ||
                            node.querySelector?.('.employee-card')) {
                            shouldReinit = true;
                        }
                    }
                });
            }
        });
        
        if (shouldReinit) {
            console.log('🔄 DOM cambió, reinicializando...');
            setTimeout(setupSortable, 100);
        }
    });
    
    // Observar cambios
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Inicializar
    setupSortable();
    
    // Funciones globales para debugging
    window.KanbanDragDrop = {
        reinitialize: setupSortable,
        cleanup: cleanupSortable,
        showToast: showToast,
        updateCounters: updateEmployeeCounters,
        isTouchDevice: isTouchDevice,
        instanceCount: () => sortableInstances.length
    };
    
    console.log('✅ Drag & Drop inicializado correctamente');
}

// Inicializar cuando todo esté listo
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function() {
        // Esperar un poco más para asegurar que SortableJS esté cargado
        setTimeout(initializeDragDrop, 100);
    });
} else {
    // DOM ya está listo
    setTimeout(initializeDragDrop, 100);
}