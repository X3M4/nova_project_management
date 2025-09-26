console.log('🚀 Inicializando sistema de drag & drop universal...');

document.addEventListener('DOMContentLoaded', function() {
    // Variables globales
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
    if (!csrfToken) {
        console.error('❌ CSRF token no encontrado');
        return;
    }
    
    let draggedElement = null;
    let isDragging = false;
    let startPos = { x: 0, y: 0 };
    let currentPos = { x: 0, y: 0 };
    let dragThreshold = 10;
    let touchStartTime = 0;
    let isTouch = false;
    
    // Detectar dispositivo táctil
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    console.log(`📱 Dispositivo táctil detectado: ${isTouchDevice}`);
    
    // Función para mostrar notificaciones
    function showToast(message, type = 'success') {
        let toast = document.getElementById('drag-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'drag-toast';
            toast.className = 'fixed top-4 right-4 z-50 px-6 py-3 rounded-lg shadow-lg transform translate-x-full transition-all duration-300 flex items-center max-w-sm';
            document.body.appendChild(toast);
        }
        
        const bgColor = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        toast.className = toast.className.replace(/bg-\w+-500/g, '') + ' ' + bgColor;
        toast.innerHTML = message;
        
        // Mostrar
        setTimeout(() => toast.classList.remove('translate-x-full'), 10);
        
        // Ocultar
        setTimeout(() => {
            toast.classList.add('translate-x-full');
        }, 4000);
    }
    
    // Función para obtener coordenadas del evento
    function getEventCoords(e) {
        if (e.touches && e.touches.length > 0) {
            return { x: e.touches[0].clientX, y: e.touches[0].clientY };
        }
        return { x: e.clientX, y: e.clientY };
    }
    
    // Función para crear elemento ghost durante el drag
    function createDragGhost(element) {
        const ghost = element.cloneNode(true);
        ghost.id = 'drag-ghost';
        ghost.style.cssText = `
            position: fixed;
            top: -1000px;
            left: -1000px;
            width: ${element.offsetWidth}px;
            height: ${element.offsetHeight}px;
            opacity: 0.8;
            transform: rotate(3deg) scale(1.05);
            z-index: 9999;
            pointer-events: none;
            box-shadow: 0 10px 25px rgba(0,0,0,0.3);
            border: 2px solid #3b82f6;
        `;
        document.body.appendChild(ghost);
        return ghost;
    }
    
    // Función para actualizar posición del ghost
    function updateGhostPosition(x, y, ghost) {
        if (ghost) {
            ghost.style.left = (x - ghost.offsetWidth / 2) + 'px';
            ghost.style.top = (y - ghost.offsetHeight / 2) + 'px';
        }
    }
    
    // Función para encontrar la zona de drop bajo el cursor
    function findDropZone(x, y) {
        const elements = document.elementsFromPoint(x, y);
        
        for (let element of elements) {
            // Buscar columna de proyecto
            const projectColumn = element.closest('.project-column');
            if (projectColumn) {
                const kanbanColumn = projectColumn.querySelector('.kanban-column');
                if (kanbanColumn) {
                    return {
                        element: kanbanColumn,
                        projectId: kanbanColumn.dataset.projectId,
                        type: 'project'
                    };
                }
            }
            
            // Buscar columna de sin asignar
            const unassignedColumn = element.closest('.kanban-column:not([data-project-id])');
            if (unassignedColumn) {
                return {
                    element: unassignedColumn,
                    projectId: null,
                    type: 'unassigned'
                };
            }
        }
        
        return null;
    }
    
    // Función para resaltar zona de drop
    function highlightDropZone(dropZone, highlight = true) {
        if (!dropZone) return;
        
        const projectColumn = dropZone.element.closest('.project-column');
        if (projectColumn) {
            if (highlight) {
                projectColumn.classList.add('drop-hover');
                projectColumn.style.background = 'linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(59, 130, 246, 0.2))';
                projectColumn.style.transform = 'scale(1.02)';
                projectColumn.style.transition = 'all 0.2s ease';
            } else {
                projectColumn.classList.remove('drop-hover');
                projectColumn.style.background = '';
                projectColumn.style.transform = '';
            }
        }
    }
    
    // Función para limpiar todas las visualizaciones
    function clearAllVisuals() {
        document.querySelectorAll('.project-column, .kanban-column').forEach(col => {
            col.classList.remove('drop-hover', 'drag-over');
            col.style.background = '';
            col.style.transform = '';
        });
        
        document.querySelectorAll('.employee-card').forEach(card => {
            card.classList.remove('dragging', 'drag-preview');
        });
        
        const ghost = document.getElementById('drag-ghost');
        if (ghost) ghost.remove();
    }
    
    // Función para realizar el drop
    function performDrop(employeeId, projectId, employeeName) {
        console.log(`🎯 Realizando drop: empleado ${employeeId} → proyecto ${projectId || 'sin asignar'}`);
        
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
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                const projectName = projectId ? 
                    document.querySelector(`[data-project-id="${projectId}"]`)?.closest('.project-column')?.querySelector('.project-title, h3')?.textContent?.trim() || `Proyecto ${projectId}` :
                    'Sin asignar';
                
                showToast(`<i class="fas fa-check-circle mr-2"></i>${employeeName} → ${projectName}`, 'success');
                
                // Recargar página después de un breve delay
                setTimeout(() => window.location.reload(), 2000);
            } else {
                throw new Error(data.error || 'Error desconocido');
            }
        })
        .catch(error => {
            console.error('❌ Error:', error);
            showToast(`<i class="fas fa-exclamation-triangle mr-2"></i>Error: ${error.message}`, 'error');
        });
    }
    
    // Configurar event listeners para todas las tarjetas de empleados
    function setupEmployeeCards() {
        const employeeCards = document.querySelectorAll('.employee-card[data-employee-id]');
        console.log(`🎯 Configurando ${employeeCards.length} tarjetas de empleados...`);
        
        employeeCards.forEach(card => {
            const employeeId = card.dataset.employeeId;
            const employeeName = card.querySelector('h4')?.textContent?.trim() || 'Empleado';
            
            // Asegurar que el ID sea limpio
            if (!employeeId || employeeId.includes('<') || employeeId.includes('>')) {
                console.warn('⚠️ Tarjeta con ID inválido:', employeeId);
                return;
            }
            
            console.log(`📝 Configurando empleado: ${employeeName} (ID: ${employeeId})`);
            
            // Eventos de ratón
            card.addEventListener('mousedown', handleStart);
            card.addEventListener('dragstart', e => e.preventDefault()); // Deshabilitar drag nativo
            
            // Eventos táctiles
            card.addEventListener('touchstart', handleStart, { passive: false });
            
            function handleStart(e) {
                if (e.target.closest('a') || e.target.closest('button')) return;
                
                isTouch = e.type.includes('touch');
                touchStartTime = Date.now();
                
                const coords = getEventCoords(e);
                startPos = coords;
                currentPos = coords;
                
                draggedElement = card;
                
                // Visual feedback inmediato
                card.style.transform = 'scale(1.05)';
                card.style.transition = 'transform 0.1s ease';
                
                if (isTouch) {
                    document.addEventListener('touchmove', handleMove, { passive: false });
                    document.addEventListener('touchend', handleEnd);
                } else {
                    document.addEventListener('mousemove', handleMove);
                    document.addEventListener('mouseup', handleEnd);
                }
                
                e.preventDefault();
            }
            
            function handleMove(e) {
                if (!draggedElement) return;
                
                const coords = getEventCoords(e);
                currentPos = coords;
                
                const deltaX = Math.abs(coords.x - startPos.x);
                const deltaY = Math.abs(coords.y - startPos.y);
                const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                
                if (!isDragging && distance > dragThreshold) {
                    isDragging = true;
                    
                    // Crear ghost element
                    const ghost = createDragGhost(card);
                    
                    // Visual feedback
                    card.classList.add('dragging');
                    card.style.opacity = '0.5';
                    
                    console.log(`🎬 Iniciando drag de ${employeeName}`);
                }
                
                if (isDragging) {
                    const ghost = document.getElementById('drag-ghost');
                    updateGhostPosition(coords.x, coords.y, ghost);
                    
                    // Encontrar zona de drop
                    const dropZone = findDropZone(coords.x, coords.y);
                    
                    // Limpiar highlights anteriores
                    document.querySelectorAll('.drop-hover').forEach(el => {
                        highlightDropZone({ element: el }, false);
                    });
                    
                    // Highlight nueva zona
                    if (dropZone) {
                        highlightDropZone(dropZone, true);
                    }
                    
                    e.preventDefault();
                }
            }
            
            function handleEnd(e) {
                const endTime = Date.now();
                const duration = endTime - touchStartTime;
                
                if (isTouch) {
                    document.removeEventListener('touchmove', handleMove);
                    document.removeEventListener('touchend', handleEnd);
                } else {
                    document.removeEventListener('mousemove', handleMove);
                    document.removeEventListener('mouseup', handleEnd);
                }
                
                if (isDragging) {
                    const coords = getEventCoords(e.changedTouches?.[0] || e);
                    const dropZone = findDropZone(coords.x, coords.y);
                    
                    if (dropZone) {
                        const currentProject = card.closest('.kanban-column')?.dataset.projectId || null;
                        const newProject = dropZone.projectId;
                        
                        if (currentProject !== newProject) {
                            performDrop(employeeId, newProject, employeeName);
                        } else {
                            showToast(`<i class="fas fa-info-circle mr-2"></i>${employeeName} ya está en esa ubicación`, 'info');
                        }
                    } else {
                        showToast(`<i class="fas fa-exclamation-triangle mr-2"></i>Zona de drop no válida`, 'error');
                    }
                    
                    console.log(`🏁 Finalizando drag de ${employeeName}`);
                } else if (isTouch && duration < 300) {
                    // Tap rápido en móvil - mostrar info
                    showToast(`<i class="fas fa-info-circle mr-2"></i>${employeeName}<br><small>Mantén presionado para mover</small>`, 'info');
                }
                
                // Limpiar todo
                clearAllVisuals();
                draggedElement = null;
                isDragging = false;
                isTouch = false;
            }
        });
    }
    
    // Inicializar
    setupEmployeeCards();
    
    // Observar cambios en el DOM
    const observer = new MutationObserver(() => {
        console.log('🔄 DOM cambió, reconfigurando tarjetas...');
        setTimeout(setupEmployeeCards, 100);
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Mensaje de bienvenida
    setTimeout(() => {
        const message = isTouchDevice ? 
            '<i class="fas fa-mobile-alt mr-2"></i>Mantén presionado para mover empleados' :
            '<i class="fas fa-mouse-pointer mr-2"></i>Arrastra empleados entre proyectos';
        showToast(message, 'info');
    }, 1000);
    
    // Exponer funciones para debugging
    window.DragDropDebug = {
        showToast,
        clearAllVisuals,
        setupEmployeeCards,
        isTouchDevice
    };
    
    console.log('✅ Sistema de drag & drop universal inicializado');
});