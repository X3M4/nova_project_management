console.log('🚀 Inicializando sistema de drag & drop optimizado...');

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
    let currentDropZone = null;
    let dragThreshold = 8;
    let touchStartTime = 0;
    let isTouch = false;
    let moveTimeout = null;
    
    // Detectar dispositivo táctil
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;
    console.log(`📱 Dispositivo táctil detectado: ${isTouchDevice}`);
    
    // Función optimizada para mostrar notificaciones
    function showToast(message, type = 'success', duration = 3000) {
        let toast = document.getElementById('drag-toast');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'drag-toast';
            toast.className = 'toast fixed top-4 right-4 z-50 px-4 py-3 rounded-lg shadow-lg transform translate-x-full transition-all duration-300 flex items-center max-w-sm';
            document.body.appendChild(toast);
        }
        
        // Limpiar clases de color anteriores
        toast.className = toast.className.replace(/bg-\w+-500/g, '').replace(/border-l-\w+-500/g, '');
        
        // Agregar nuevas clases
        const colorClass = type === 'success' ? 'bg-green-500' : type === 'error' ? 'bg-red-500' : 'bg-blue-500';
        toast.classList.add(colorClass, 'text-white');
        toast.innerHTML = message;
        
        // Mostrar con requestAnimationFrame para mejor performance
        requestAnimationFrame(() => {
            toast.classList.remove('translate-x-full');
            toast.classList.add('show');
        });
        
        // Ocultar después del duration
        setTimeout(() => {
            toast.classList.add('translate-x-full');
            toast.classList.remove('show');
        }, duration);
    }
    
    // Función para obtener coordenadas optimizada
    function getEventCoords(e) {
        const touch = e.touches?.[0] || e.changedTouches?.[0];
        return touch ? { x: touch.clientX, y: touch.clientY } : { x: e.clientX, y: e.clientY };
    }
    
    // Función para crear ghost optimizado
    function createDragGhost(element) {
        const ghost = element.cloneNode(true);
        ghost.id = 'drag-ghost';
        
        // Estilos optimizados para mejor performance
        Object.assign(ghost.style, {
            position: 'fixed',
            top: '-1000px',
            left: '-1000px',
            width: element.offsetWidth + 'px',
            height: element.offsetHeight + 'px',
            opacity: '0.9',
            transform: 'rotate(3deg) scale(1.05)',
            zIndex: '9999',
            pointerEvents: 'none',
            boxShadow: '0 20px 40px rgba(0,0,0,0.3)',
            border: '2px solid var(--kanban-primary)',
            borderRadius: 'var(--kanban-border-radius)',
            background: 'white',
            willChange: 'transform',
            backfaceVisibility: 'hidden',
        });
        
        // Limpiar IDs duplicados
        ghost.removeAttribute('data-employee-id');
        ghost.querySelectorAll('[id]').forEach(el => el.removeAttribute('id'));
        
        document.body.appendChild(ghost);
        return ghost;
    }
    
    // Función optimizada para actualizar posición del ghost
    function updateGhostPosition(x, y, ghost) {
        if (!ghost) return;
        
        // Usar transform para mejor performance
        const offsetX = ghost.offsetWidth / 2;
        const offsetY = ghost.offsetHeight / 2;
        ghost.style.transform = `translate3d(${x - offsetX}px, ${y - offsetY}px, 0) rotate(3deg) scale(1.05)`;
    }
    
    // 🔧 FUNCIÓN MEJORADA para encontrar zona de drop
    function findDropZone(x, y) {
        const elements = document.elementsFromPoint(x, y);
        
        for (let element of elements) {
            // 1. Buscar columna de proyecto (kanban-column con data-project-id)
            const kanbanColumn = element.closest('.kanban-column[data-project-id]');
            if (kanbanColumn) {
                return {
                    element: kanbanColumn,
                    projectId: kanbanColumn.dataset.projectId,
                    type: 'project',
                    projectColumn: kanbanColumn.closest('.project-column'),
                    label: `Proyecto ${kanbanColumn.dataset.projectId}`
                };
            }
            
            // 2. Buscar sidebar completo (empleados sin asignar)
            const sidebar = element.closest('.kanban-sidebar');
            if (sidebar) {
                const unassignedContainer = sidebar.querySelector('.unassigned-employees');
                if (unassignedContainer) {
                    return {
                        element: unassignedContainer,
                        projectId: null,
                        type: 'unassigned',
                        projectColumn: sidebar,
                        label: 'Sin asignar'
                    };
                }
            }
            
            // 3. Buscar directamente el contenedor de empleados sin asignar
            const unassignedDirect = element.closest('.unassigned-employees');
            if (unassignedDirect) {
                return {
                    element: unassignedDirect,
                    projectId: null,
                    type: 'unassigned',
                    projectColumn: unassignedDirect.closest('.kanban-sidebar') || unassignedDirect.parentElement,
                    label: 'Sin asignar'
                };
            }
        }
        
        return null;
    }
    
    // Función optimizada para highlight con debounce
    let highlightTimeout = null;
    function highlightDropZone(dropZone, highlight = true) {
        if (highlightTimeout) {
            clearTimeout(highlightTimeout);
        }
        
        highlightTimeout = setTimeout(() => {
            if (!dropZone?.projectColumn) return;
            
            if (highlight) {
                dropZone.projectColumn.classList.add('drop-hover');
                dropZone.element.classList.add('drop-zone-active');
                console.log(`🎯 Highlighting drop zone: ${dropZone.label}`);
            } else {
                dropZone.projectColumn.classList.remove('drop-hover');
                dropZone.element.classList.remove('drop-zone-active');
            }
        }, 16); // 60fps
    }
    
    // Función para limpiar visuales optimizada
    function clearAllVisuals() {
        requestAnimationFrame(() => {
            document.querySelectorAll('.drop-hover, .drop-zone-active').forEach(el => {
                el.classList.remove('drop-hover', 'drop-zone-active');
            });
            
            document.querySelectorAll('.employee-card.dragging, .employee-card.drag-preview').forEach(card => {
                card.classList.remove('dragging', 'drag-preview');
                card.style.transform = '';
                card.style.opacity = '';
            });
            
            const ghost = document.getElementById('drag-ghost');
            if (ghost) ghost.remove();
        });
    }
    
    // 🔧 FUNCIÓN CORREGIDA para mover DOM sin duplicación
    function moveEmployeeCard(employeeCard, targetColumn, sourceColumn) {
        return new Promise((resolve) => {
            console.log('🔄 Moviendo tarjeta en DOM...', {
                from: sourceColumn?.className || 'unknown',
                to: targetColumn?.className || 'unknown'
            });
            
            // Verificar que los contenedores existen
            if (!targetColumn || !sourceColumn || !employeeCard) {
                console.error('❌ Error: elementos requeridos no encontrados');
                resolve(false);
                return;
            }
            
            requestAnimationFrame(() => {
                try {
                    // 1. REMOVER la tarjeta del contenedor original INMEDIATAMENTE
                    if (employeeCard.parentNode === sourceColumn) {
                        sourceColumn.removeChild(employeeCard);
                        console.log('✅ Tarjeta removida del origen');
                    }
                    
                    // 2. Agregar al nuevo contenedor
                    targetColumn.appendChild(employeeCard);
                    console.log('✅ Tarjeta añadida al destino');
                    
                    // 3. Animar la aparición
                    employeeCard.style.opacity = '0';
                    employeeCard.style.transform = 'translateY(-20px)';
                    
                    requestAnimationFrame(() => {
                        employeeCard.style.transition = 'all 0.3s ease-out';
                        employeeCard.style.opacity = '1';
                        employeeCard.style.transform = 'translateY(0)';
                        
                        setTimeout(() => {
                            employeeCard.style.transition = '';
                            employeeCard.style.transform = '';
                            resolve(true);
                        }, 300);
                    });
                    
                } catch (error) {
                    console.error('❌ Error moviendo tarjeta:', error);
                    resolve(false);
                }
            });
        });
    }
    
    // Función para actualizar contadores optimizada
    function updateEmployeeCounters() {
        requestAnimationFrame(() => {
            // Actualizar contadores de proyectos
            document.querySelectorAll('.kanban-column[data-project-id]').forEach(column => {
                const employeeCards = column.querySelectorAll('.employee-card');
                const projectColumn = column.closest('.project-column');
                const counter = projectColumn?.querySelector('.employee-count');
                if (counter) {
                    counter.textContent = `(${employeeCards.length})`;
                    console.log(`📊 Proyecto ${column.dataset.projectId}: ${employeeCards.length} empleados`);
                }
            });
            
            // Actualizar contador de sin asignar
            const unassignedColumn = document.querySelector('.unassigned-employees');
            if (unassignedColumn) {
                const employeeCards = unassignedColumn.querySelectorAll('.employee-card');
                const counter = document.querySelector('.kanban-sidebar .employee-count');
                if (counter) {
                    counter.textContent = `(${employeeCards.length})`;
                    console.log(`📊 Sin asignar: ${employeeCards.length} empleados`);
                }
            }
        });
    }
    
    // 🔧 FUNCIÓN CORREGIDA para realizar el drop
    async function performDrop(employeeId, projectId, employeeName, employeeCard, targetColumn, sourceColumn, dropZone) {
        console.log(`🎯 Realizando drop:`, {
            employee: `${employeeName} (ID: ${employeeId})`,
            from: sourceColumn?.className || 'unknown',
            to: dropZone.label,
            projectId: projectId
        });
        
        // Mostrar feedback inmediato
        showToast(`<i class="fas fa-spinner fa-spin mr-2"></i>Moviendo ${employeeName}...`, 'info', 2000);
        
        try {
            // 1. Mover en DOM INMEDIATAMENTE para evitar duplicación
            const moved = await moveEmployeeCard(employeeCard, targetColumn, sourceColumn);
            if (!moved) {
                throw new Error('Error moviendo tarjeta en DOM');
            }
            
            // 2. Actualizar contadores
            updateEmployeeCounters();
            
            // 3. Hacer petición al servidor
            const response = await fetch('/api/update-employee-project/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                body: JSON.stringify({
                    employee_id: parseInt(employeeId),
                    project_id: projectId ? parseInt(projectId) : null
                })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            
            const data = await response.json();
            
            if (data.success) {
                showToast(`<i class="fas fa-check-circle mr-2"></i>${employeeName} → ${dropZone.label}`, 'success');
                console.log(`✅ Drop completado exitosamente`);
            } else {
                throw new Error(data.error || 'Error del servidor');
            }
            
        } catch (error) {
            console.error('❌ Error en performDrop:', error);
            
            // 🔧 REVERTIR: Mover la tarjeta de vuelta al origen
            try {
                if (sourceColumn && targetColumn.contains(employeeCard)) {
                    await moveEmployeeCard(employeeCard, sourceColumn, targetColumn);
                    updateEmployeeCounters();
                }
            } catch (revertError) {
                console.error('❌ Error revirtiendo cambios:', revertError);
                // Si no se puede revertir, recargar la página
                showToast('Error crítico. Recargando página...', 'error', 2000);
                setTimeout(() => window.location.reload(), 2000);
                return;
            }
            
            showToast(`<i class="fas fa-exclamation-triangle mr-2"></i>Error: ${error.message}`, 'error');
        }
    }
    
    // Función principal para configurar tarjetas
    function setupEmployeeCards() {
        const employeeCards = document.querySelectorAll('.employee-card[data-employee-id]');
        console.log(`🎯 Configurando ${employeeCards.length} tarjetas de empleados...`);
        
        employeeCards.forEach(card => {
            const employeeId = card.dataset.employeeId;
            const employeeName = card.querySelector('.employee-name, h4')?.textContent?.trim() || 'Empleado';
            
            // Validar ID
            if (!employeeId || employeeId.includes('<') || employeeId.includes('>')) {
                console.warn('⚠️ Tarjeta con ID inválido:', employeeId);
                return;
            }
            
            // 🔧 PREVENIR duplicación de listeners
            if (card.dataset.dragConfigured === 'true') {
                return; // Ya configurada
            }
            card.dataset.dragConfigured = 'true';
            
            console.log(`📝 Configurando empleado: ${employeeName} (ID: ${employeeId})`);
            
            // Configurar estilos iniciales
            card.style.cursor = 'grab';
            card.setAttribute('tabindex', '0');
            card.setAttribute('role', 'button');
            card.setAttribute('aria-label', `Arrastrar ${employeeName}`);
            
            let startCoords = null;
            let moveCount = 0;
            
            // Función para manejar inicio
            function handleStart(e) {
                if (e.target.closest('a, button, input, select, textarea')) {
                    return;
                }
                
                isTouch = e.type.includes('touch');
                touchStartTime = Date.now();
                startCoords = getEventCoords(e);
                moveCount = 0;
                
                draggedElement = card;
                
                // Feedback visual inmediato
                card.style.transform = 'scale(1.02)';
                card.style.transition = 'transform 0.1s ease';
                
                // Event listeners
                if (isTouch) {
                    document.addEventListener('touchmove', handleMove, { passive: false });
                    document.addEventListener('touchend', handleEnd, { passive: true });
                } else {
                    document.addEventListener('mousemove', handleMove, { passive: true });
                    document.addEventListener('mouseup', handleEnd, { passive: true });
                }
                
                e.preventDefault();
            }
            
            // Función para manejar movimiento
            function handleMove(e) {
                if (!draggedElement || !startCoords) return;
                
                moveCount++;
                
                // Throttling
                if (moveCount % 3 !== 0) return;
                
                const coords = getEventCoords(e);
                const deltaX = Math.abs(coords.x - startCoords.x);
                const deltaY = Math.abs(coords.y - startCoords.y);
                const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY);
                
                if (!isDragging && distance > dragThreshold) {
                    isDragging = true;
                    
                    // Crear ghost
                    const ghost = createDragGhost(card);
                    
                    // Visual feedback
                    card.classList.add('dragging');
                    card.style.opacity = '0.5';
                    card.style.cursor = 'grabbing';
                    
                    console.log(`🎬 Iniciando drag de ${employeeName}`);
                }
                
                if (isDragging) {
                    // Actualizar ghost position
                    const ghost = document.getElementById('drag-ghost');
                    updateGhostPosition(coords.x, coords.y, ghost);
                    
                    // Drop zone detection
                    if (moveTimeout) clearTimeout(moveTimeout);
                    moveTimeout = setTimeout(() => {
                        const dropZone = findDropZone(coords.x, coords.y);
                        
                        if (currentDropZone !== dropZone) {
                            // Limpiar highlight anterior
                            if (currentDropZone) {
                                highlightDropZone(currentDropZone, false);
                            }
                            
                            // Aplicar nuevo highlight
                            if (dropZone) {
                                highlightDropZone(dropZone, true);
                            }
                            
                            currentDropZone = dropZone;
                        }
                    }, 16);
                    
                    e.preventDefault();
                }
            }
            
            // Función para manejar fin
            async function handleEnd(e) {
                const endTime = Date.now();
                const duration = endTime - touchStartTime;
                
                // Limpiar listeners
                if (isTouch) {
                    document.removeEventListener('touchmove', handleMove);
                    document.removeEventListener('touchend', handleEnd);
                } else {
                    document.removeEventListener('mousemove', handleMove);
                    document.removeEventListener('mouseup', handleEnd);
                }
                
                if (isDragging) {
                    const dropZone = currentDropZone;
                    
                    if (dropZone) {
                        // 🔧 OBTENER contenedores correctamente
                        const sourceColumn = card.closest('.kanban-column, .unassigned-employees');
                        const currentProject = sourceColumn?.dataset.projectId || null;
                        const newProject = dropZone.projectId;
                        
                        console.log('📋 Comparando proyectos:', { current: currentProject, new: newProject });
                        
                        if (currentProject !== newProject) {
                            const targetColumn = dropZone.element;
                            
                            // Validar que los contenedores son correctos
                            if (!sourceColumn || !targetColumn) {
                                console.error('❌ Contenedores no válidos:', { sourceColumn, targetColumn });
                                showToast('Error: Contenedores no válidos', 'error');
                            } else {
                                await performDrop(employeeId, newProject, employeeName, card, targetColumn, sourceColumn, dropZone);
                            }
                        } else {
                            showToast(`<i class="fas fa-info-circle mr-2"></i>${employeeName} ya está en ${dropZone.label}`, 'info', 2000);
                        }
                    } else {
                        showToast(`<i class="fas fa-exclamation-triangle mr-2"></i>Zona de drop no válida`, 'error', 2000);
                    }
                    
                    console.log(`🏁 Finalizando drag de ${employeeName}`);
                } else if (isTouch && duration < 300 && moveCount < 5) {
                    // Tap rápido - mostrar info
                    showToast(`<i class="fas fa-info-circle mr-2"></i>${employeeName}<br><small>Mantén presionado para mover</small>`, 'info', 2000);
                }
                
                // Limpiar todo
                clearAllVisuals();
                draggedElement = null;
                isDragging = false;
                isTouch = false;
                currentDropZone = null;
                startCoords = null;
                moveCount = 0;
                
                if (moveTimeout) {
                    clearTimeout(moveTimeout);
                    moveTimeout = null;
                }
                
                // Restaurar cursor
                card.style.cursor = 'grab';
            }
            
            // Event listeners principales
            card.addEventListener('mousedown', handleStart, { passive: false });
            card.addEventListener('touchstart', handleStart, { passive: false });
            
            // Prevenir drag nativo
            card.addEventListener('dragstart', e => e.preventDefault());
        });
    }
    
    // Inicializar
    setupEmployeeCards();
    updateEmployeeCounters();
    
    // Observer optimizado
    let observerTimeout = null;
    const observer = new MutationObserver((mutations) => {
        if (observerTimeout) clearTimeout(observerTimeout);
        observerTimeout = setTimeout(() => {
            if (!isDragging) {
                // Solo reconfigurar si se añadieron nuevas tarjetas
                const hasNewCards = Array.from(mutations).some(mutation => 
                    Array.from(mutation.addedNodes).some(node => 
                        node.nodeType === 1 && (
                            node.classList?.contains('employee-card') || 
                            node.querySelector?.('.employee-card')
                        )
                    )
                );
                
                if (hasNewCards) {
                    console.log('🔄 Nuevas tarjetas detectadas, reconfigurando...');
                    setupEmployeeCards();
                }
            }
        }, 250);
    });
    
    observer.observe(document.body, {
        childList: true,
        subtree: true
    });
    
    // Mensaje de bienvenida
    setTimeout(() => {
        const message = isTouchDevice ? 
            '<i class="fas fa-mobile-alt mr-2"></i>Mantén presionado para mover empleados' :
            '<i class="fas fa-mouse-pointer mr-2"></i>Arrastra empleados entre columnas';
        showToast(message, 'info', 4000);
    }, 1000);
    
    // Funciones de debugging
    window.DragDropDebug = {
        showToast,
        clearAllVisuals,
        setupEmployeeCards,
        updateCounters: updateEmployeeCounters,
        isTouchDevice,
        reloadPage: () => window.location.reload(),
        testDropZones: () => {
            console.log('🔍 Testeando zonas de drop...');
            document.querySelectorAll('.kanban-column[data-project-id]').forEach(col => {
                console.log(`Proyecto: ${col.dataset.projectId}`, col);
            });
            const unassigned = document.querySelector('.unassigned-employees');
            console.log('Sin asignar:', unassigned);
        }
    };
    
    console.log('✅ Sistema de drag & drop optimizado inicializado');
});