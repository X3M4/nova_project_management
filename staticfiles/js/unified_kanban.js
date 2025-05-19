document.addEventListener('DOMContentLoaded', function() {
    console.log('Unified Kanban script loaded');
    
    // Variables básicas
    const columns = document.querySelectorAll('.kanban-column');
    const projectColumns = document.querySelectorAll('.project-column');
    const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const loadingIndicator = document.getElementById('loading-indicator');
    const toastNotification = document.getElementById('toast-notification');
    const toggleSidebarBtn = document.querySelector('.toggle-sidebar');
    const sidebar = document.querySelector('.sidebar');
    
    // Determinar tipo de dispositivo
    const isTouchDevice = ('ontouchstart' in window) || 
                        (navigator.maxTouchPoints > 0) || 
                        (navigator.msMaxTouchPoints > 0);
    
    console.log('Touch device detected:', isTouchDevice);
    
    // Añadir clase al body para estilos específicos de táctil
    if (isTouchDevice) {
        document.body.classList.add('touch-device');
    }
    
    // Toggle sidebar en móviles
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
    
    // Función para mostrar notificaciones
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
        
        // Mostrar
        setTimeout(() => {
            toastNotification.classList.remove('translate-y-full', 'opacity-0');
        }, 10);
        
        // Ocultar después de un tiempo
        setTimeout(() => {
            toastNotification.classList.add('translate-y-full', 'opacity-0');
        }, 3000);
    }
    
    // Función para actualizar la asignación de empleado
    function updateEmployeeProject(employeeId, projectId, sourceElement, targetElement) {
        // Mostrar indicador de carga
        loadingIndicator.classList.remove('hidden');
        
        // Actualizar vía AJAX
        return fetch('/api/update-employee-project/', {
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
                // Si tenemos elementos, mover la carta al objetivo
                if (sourceElement && targetElement) {
                    targetElement.appendChild(sourceElement);
                    
                    // Eliminar mensaje de "no employees" si existe
                    const emptyMessage = targetElement.querySelector('.text-xs.text-gray-500.italic');
                    if (emptyMessage) {
                        emptyMessage.remove();
                    }
                }
                
                // Feedback háptico de éxito
                if (window.navigator.vibrate) {
                    window.navigator.vibrate([30, 20, 30]);
                }
                
                showToast('<i class="fas fa-check-circle mr-2"></i> Employee moved successfully!', 'success');
                return true;
            } else {
                // Feedback háptico de error
                if (window.navigator.vibrate) {
                    window.navigator.vibrate(150);
                }
                
                showToast(`<i class="fas fa-exclamation-triangle mr-2"></i> ${data.error || 'An error occurred'}`, 'error');
                return false;
            }
        })
        .catch(error => {
            console.error('Error:', error);
            loadingIndicator.classList.add('hidden');
            
            // Feedback háptico de error
            if (window.navigator.vibrate) {
                window.navigator.vibrate(150);
            }
            
            showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Network error occurred', 'error');
            return false;
        });
    }
    
    // MÉTODO 1: Initializar SortableJS para ambos tipos de dispositivos
    function initSortable() {
        // Lista para almacenar todas las instancias Sortable
        const sortables = [];
        
        columns.forEach(column => {
            const projectId = column.getAttribute('data-project-id');
            
            // Crear instancia de Sortable para cada columna
            const sortable = new Sortable(column, {
                group: 'shared',         // Grupo compartido para permitir arrastrar entre columnas
                animation: 150,          // Duración de la animación en ms
                easing: "cubic-bezier(0.2, 0, 0, 1)",  // Curva de animación suave
                delay: isTouchDevice ? 150 : 0,        // Delay en dispositivos táctiles para evitar conflictos
                delayOnTouchOnly: true,  // Delay solo en dispositivos táctiles
                touchStartThreshold: 10, // Umbral para iniciar arrastre, evita conflictos con scroll
                fallbackTolerance: 5,    // Tolerancia para fallback
                supportPointer: true,    // Usar pointer events para mejor compatibilidad
                forceFallback: isTouchDevice, // Forzar fallback en dispositivos táctiles
                
                // Clases de estilo
                ghostClass: 'dragging',  // Clase para el fantasma
                chosenClass: 'chosen',   // Clase para el elemento seleccionado
                dragClass: 'drag',       // Clase para el elemento durante arrastre
                
                // Eventos
                onStart: function(evt) {
                    console.log('Drag started for employee', evt.item.getAttribute('data-employee-id'));
                    
                    // Añadir clase al elemento arrastrado
                    evt.item.classList.add('dragging');
                    
                    // Resaltar todas las columnas como potenciales objetivos
                    document.querySelectorAll('.project-column').forEach(col => {
                        col.classList.add('potential-drop-area');
                    });
                    
                    // Habilitar vibración táctil si está disponible
                    if (isTouchDevice && window.navigator.vibrate) {
                        window.navigator.vibrate(30);
                    }
                },
                
                onEnd: function(evt) {
                    console.log('Drag ended');
                    const item = evt.item;
                    const employeeId = item.getAttribute('data-employee-id');
                    const newColumn = evt.to;
                    const newProjectId = newColumn.getAttribute('data-project-id');
                    const oldColumn = evt.from;
                    
                    // Limpiar clases visuales
                    item.classList.remove('dragging', 'chosen', 'drag');
                    document.querySelectorAll('.project-column').forEach(col => {
                        col.classList.remove('potential-drop-area', 'drop-hover');
                    });
                    document.querySelectorAll('.kanban-column').forEach(col => {
                        col.classList.remove('drop-hover');
                    });
                    
                    // Si la columna cambió, actualizar en el servidor
                    if (oldColumn !== newColumn) {
                        console.log(`Moving employee ${employeeId} to project ${newProjectId}`);
                        
                        // Actualizar mediante AJAX
                        updateEmployeeProject(employeeId, newProjectId, null, null)
                            .then(success => {
                                if (!success) {
                                    // Si falló, revertir el movimiento visual
                                    console.log('Move failed, reverting');
                                    oldColumn.appendChild(item);
                                }
                            });
                    }
                },
                
                onMove: function(evt) {
                    // Resaltar columna destino
                    document.querySelectorAll('.kanban-column').forEach(col => {
                        col.classList.remove('drop-hover');
                    });
                    
                    if (evt.to) {
                        evt.to.classList.add('drop-hover');
                    }
                    
                    return true; // Permitir el movimiento
                }
            });
            
            sortables.push(sortable);
            console.log(`SortableJS initialized for column with project ID: ${projectId || 'unassigned'}`);
        });
        
        return sortables;
    }
    
    // MÉTODO 2: Drag and drop nativo para dispositivos sin touch 
    // (usado como respaldo si SortableJS falla)
    function initNativeDragDrop() {
        // Solo si hay problemas con SortableJS
        const employeeCards = document.querySelectorAll('.employee-card');
        
        // Limpiar clases visuales
        function clearDragVisuals() {
            document.querySelectorAll('.employee-card').forEach(card => {
                card.classList.remove('dragging');
            });
            
            document.querySelectorAll('.project-column').forEach(col => {
                col.classList.remove('drop-hover', 'potential-drop-area');
            });
            
            document.querySelectorAll('.kanban-column').forEach(col => {
                col.classList.remove('drop-hover');
            });
        }
        
        // Añadir eventos de arrastre a cada tarjeta
        employeeCards.forEach(card => {
            // Hacer que sea arrastrable
            card.setAttribute('draggable', 'true');
            
            // Iniciar arrastre
            card.addEventListener('dragstart', function(e) {
                clearDragVisuals();
                e.dataTransfer.setData('text/plain', card.getAttribute('data-employee-id'));
                card.classList.add('dragging');
                
                // Resaltar posibles destinos
                projectColumns.forEach(col => {
                    col.classList.add('potential-drop-area');
                });
                
                console.log('Native drag started for employee:', card.getAttribute('data-employee-id'));
            });
            
            // Finalizar arrastre
            card.addEventListener('dragend', function() {
                setTimeout(clearDragVisuals, 100);
            });
        });
        
        // Eventos para columnas de proyecto
        projectColumns.forEach(projectColumn => {
            const kanbanColumn = projectColumn.querySelector('.kanban-column');
            
            if (!kanbanColumn) {
                console.error('No kanban column found in project column');
                return;
            }
            
            const projectId = kanbanColumn.getAttribute('data-project-id');
            
            // Permitir zona de suelta
            projectColumn.addEventListener('dragover', function(e) {
                e.preventDefault();
                projectColumn.classList.add('drop-hover');
            });
            
            // Quitar resaltado cuando sale
            projectColumn.addEventListener('dragleave', function(e) {
                if (!projectColumn.contains(e.relatedTarget)) {
                    projectColumn.classList.remove('drop-hover');
                }
            });
            
            // Procesar cuando sueltan un elemento
            projectColumn.addEventListener('drop', function(e) {
                e.preventDefault();
                clearDragVisuals();
                
                const employeeId = e.dataTransfer.getData('text/plain');
                
                if (!employeeId) {
                    console.error('No employee ID found in drop data');
                    return;
                }
                
                // Encontrar la tarjeta
                const card = document.querySelector(`.employee-card[data-employee-id="${employeeId}"]`);
                
                if (!card) {
                    console.error('Could not find employee card with ID:', employeeId);
                    return;
                }
                
                console.log('Native drop - Employee ID:', employeeId, 'Project ID:', projectId);
                
                // Actualizar en el servidor
                updateEmployeeProject(employeeId, projectId, card, kanbanColumn);
            });
        });
        
        // Para la columna de no asignados
        columns.forEach(column => {
            // Omitir si es parte de una columna de proyecto
            if (column.closest('.project-column')) {
                return;
            }
            
            const projectId = column.getAttribute('data-project-id');
            
            column.addEventListener('dragover', function(e) {
                e.preventDefault();
                column.classList.add('drop-hover');
            });
            
            column.addEventListener('dragleave', function(e) {
                if (!column.contains(e.relatedTarget)) {
                    column.classList.remove('drop-hover');
                }
            });
            
            column.addEventListener('drop', function(e) {
                e.preventDefault();
                clearDragVisuals();
                
                const employeeId = e.dataTransfer.getData('text/plain');
                
                if (!employeeId) {
                    console.error('No employee ID found in drop data');
                    return;
                }
                
                // Encontrar la tarjeta
                const card = document.querySelector(`.employee-card[data-employee-id="${employeeId}"]`);
                
                if (!card) {
                    console.error('Could not find employee card with ID:', employeeId);
                    return;
                }
                
                console.log('Native drop on unassigned - Employee ID:', employeeId, 'Project ID:', projectId);
                
                // Actualizar en el servidor
                updateEmployeeProject(employeeId, projectId, card, column);
            });
        });
        
        // Limpiar estados cuando cambia la visibilidad
        document.addEventListener('visibilitychange', function() {
            if (document.visibilityState === 'visible') {
                clearDragVisuals();
            }
        });
        
        console.log('Native drag and drop initialized as fallback');
    }
    
    // MÉTODO 3: Solución específica para táctil con eventos touch
    function initTouchDragDrop() {
        if (!isTouchDevice) return;
        
        // Variables para arrastre táctil
        let touchDragging = false;
        let draggedElement = null;
        let touchOffsetX = 0;
        let touchOffsetY = 0;
        let startTime = 0;
        let startX = 0;
        let startY = 0;
        let targetColumn = null;
        let dragOverlay = null;
        
        // Crear un overlay para arrastre
        function createOverlay() {
            const overlay = document.createElement('div');
            overlay.className = 'touch-drag-overlay';
            overlay.style.position = 'fixed';
            overlay.style.top = '0';
            overlay.style.left = '0';
            overlay.style.width = '100%';
            overlay.style.height = '100%';
            overlay.style.backgroundColor = 'rgba(0,0,0,0)'; // Transparente
            overlay.style.zIndex = '9999';
            overlay.style.pointerEvents = 'none'; // No bloquear eventos
            
            return overlay;
        }
        
        // Crear un clon visual para arrastrar
        function createDragVisual(element) {
            const rect = element.getBoundingClientRect();
            const visual = element.cloneNode(true);
            
            visual.style.position = 'fixed';
            visual.style.width = rect.width + 'px';
            visual.style.pointerEvents = 'none';
            visual.style.zIndex = '10000';
            visual.style.opacity = '0.8';
            visual.style.boxShadow = '0 10px 15px rgba(0,0,0,0.2)';
            visual.style.transform = 'scale(1.05)';
            
            return visual;
        }
        
        // Encontrar columna debajo de un punto
        function findColumnAtPoint(x, y) {
            // Ocultar temporalmente el elemento visual para que no bloquee
            if (dragOverlay && dragOverlay.firstChild) {
                dragOverlay.firstChild.style.display = 'none';
            }
            
            // Encontrar elemento debajo
            const element = document.elementFromPoint(x, y);
            
            // Restaurar visibilidad
            if (dragOverlay && dragOverlay.firstChild) {
                dragOverlay.firstChild.style.display = '';
            }
            
            if (!element) return null;
            
            // Buscar columna kanban padre
            return element.closest('.kanban-column');
        }
        
        // Marcar todas las tarjetas como arrastrables para táctil
        document.querySelectorAll('.employee-card').forEach(card => {
            // Indicador visual de que es arrastrable
            card.classList.add('touch-draggable');
            
            // Iniciar arrastre con toque largo
            card.addEventListener('touchstart', function(e) {
                // Ignorar si tocamos un enlace o botón
                if (e.target.closest('a') || e.target.closest('button')) {
                    return;
                }
                
                const touch = e.touches[0];
                startX = touch.clientX;
                startY = touch.clientY;
                startTime = Date.now();
                
                // Configurar timeout para iniciar arrastre después de mantener presionado
                card.touchTimeout = setTimeout(function() {
                    // Vibrar para indicar que comenzó el arrastre
                    if (window.navigator.vibrate) {
                        window.navigator.vibrate(50);
                    }
                    
                    touchDragging = true;
                    draggedElement = card;
                    
                    // Crear overlay
                    dragOverlay = createOverlay();
                    document.body.appendChild(dragOverlay);
                    
                    // Crear visual de arrastre
                    const dragVisual = createDragVisual(card);
                    dragOverlay.appendChild(dragVisual);
                    
                    // Posicionar en la posición del toque
                    const rect = card.getBoundingClientRect();
                    touchOffsetX = touch.clientX - rect.left;
                    touchOffsetY = touch.clientY - rect.top;
                    dragVisual.style.left = (touch.clientX - touchOffsetX) + 'px';
                    dragVisual.style.top = (touch.clientY - touchOffsetY) + 'px';
                    
                    // Semi-ocultar la carta original
                    card.style.opacity = '0.4';
                    
                    // Marcar columnas como potenciales destinos
                    document.querySelectorAll('.project-column').forEach(col => {
                        col.classList.add('potential-drop-area');
                    });
                    
                    console.log('Touch drag started for:', card.getAttribute('data-employee-id'));
                }, 500); // 500ms es un buen tiempo para toque largo
            });
            
            // Mover mientras arrastramos
            card.addEventListener('touchmove', function(e) {
                if (!touchDragging || !draggedElement || !dragOverlay) {
                    // Si hay un timeout pendiente y el usuario se mueve significativamente, cancelarlo
                    if (card.touchTimeout) {
                        const touch = e.touches[0];
                        const moveX = Math.abs(touch.clientX - startX);
                        const moveY = Math.abs(touch.clientY - startY);
                        
                        if (moveX > 10 || moveY > 10) {
                            clearTimeout(card.touchTimeout);
                            card.touchTimeout = null;
                        }
                    }
                    return;
                }
                
                e.preventDefault(); // Evitar scroll
                
                const touch = e.touches[0];
                
                // Mover el visual
                const dragVisual = dragOverlay.firstChild;
                if (dragVisual) {
                    dragVisual.style.left = (touch.clientX - touchOffsetX) + 'px';
                    dragVisual.style.top = (touch.clientY - touchOffsetY) + 'px';
                }
                
                // Detectar columna debajo
                const column = findColumnAtPoint(touch.clientX, touch.clientY);
                
                // Resaltar columna actual
                document.querySelectorAll('.kanban-column').forEach(col => {
                    col.classList.remove('drop-hover');
                });
                
                if (column) {
                    column.classList.add('drop-hover');
                    targetColumn = column;
                } else {
                    targetColumn = null;
                }
            });
            
            // Terminar arrastre
            card.addEventListener('touchend', function(e) {
                // Limpiar cualquier timeout pendiente
                if (card.touchTimeout) {
                    clearTimeout(card.touchTimeout);
                    card.touchTimeout = null;
                }
                
                // Si no estábamos arrastrando, salir
                if (!touchDragging || !draggedElement) {
                    return;
                }
                
                // Restaurar opacidad
                card.style.opacity = '';
                
                // Remover overlay
                if (dragOverlay) {
                    document.body.removeChild(dragOverlay);
                    dragOverlay = null;
                }
                
                // Si tenemos una columna objetivo válida
                if (targetColumn) {
                    const employeeId = card.getAttribute('data-employee-id');
                    const projectId = targetColumn.getAttribute('data-project-id');
                    
                    console.log('Touch drop - Employee ID:', employeeId, 'Project ID:', projectId);
                    
                    // Actualizar en el servidor
                    updateEmployeeProject(employeeId, projectId, card, targetColumn);
                }
                
                // Limpiar estados
                touchDragging = false;
                draggedElement = null;
                targetColumn = null;
                
                // Limpiar clases visuales
                document.querySelectorAll('.employee-card').forEach(c => {
                    c.classList.remove('dragging');
                });
                
                document.querySelectorAll('.project-column').forEach(col => {
                    col.classList.remove('potential-drop-area', 'drop-hover');
                });
                
                document.querySelectorAll('.kanban-column').forEach(col => {
                    col.classList.remove('drop-hover');
                });
            });
        });
        
        // Crear botón flotante de ayuda
        const helpButton = document.createElement('button');
        helpButton.innerHTML = '<i class="fas fa-hand-pointer"></i>';
        helpButton.className = 'fixed bottom-4 left-4 bg-blue-600 text-white rounded-full w-12 h-12 flex items-center justify-center shadow-lg z-50';
        helpButton.addEventListener('click', function() {
            showToast('<i class="fas fa-hand-pointer mr-2"></i> Mantén presionado y arrastra para mover empleados', 'info');
        });
        
        document.body.appendChild(helpButton);
        
        // Mostrar instrucción inicial
        if (!localStorage.getItem('touch-drag-instruction-shown')) {
            setTimeout(() => {
                showToast('<i class="fas fa-hand-pointer mr-2"></i> Mantén presionado y arrastra para mover empleados', 'info');
                localStorage.setItem('touch-drag-instruction-shown', 'true');
            }, 1000);
        }
        
        console.log('Touch-specific drag and drop initialized');
    }
    
    // Habilitar scroll por arrastre en los contenedores
    function enableDragScroll() {
        // Contenedor principal de proyectos (scroll horizontal)
        document.querySelectorAll('.projects-container').forEach(container => {
            let isDown = false;
            let startX;
            let scrollLeft;
            
            container.addEventListener('mousedown', (e) => {
                // No iniciar si estamos en una tarjeta o botón
                if (e.target.closest('.employee-card') || 
                    e.target.closest('button') || 
                    e.target.closest('a')) return;
                
                isDown = true;
                container.style.cursor = 'grabbing';
                startX = e.pageX - container.offsetLeft;
                scrollLeft = container.scrollLeft;
            });
            
            container.addEventListener('mouseleave', () => {
                isDown = false;
                container.style.cursor = 'grab';
            });
            
            container.addEventListener('mouseup', () => {
                isDown = false;
                container.style.cursor = 'grab';
            });
            
            container.addEventListener('mousemove', (e) => {
                if (!isDown) return;
                
                const x = e.pageX - container.offsetLeft;
                const walk = (x - startX) * 2;
                container.scrollLeft = scrollLeft - walk;
            });
            
            // Indicador visual para scroll táctil
            if (isTouchDevice) {
                const indicator = document.createElement('div');
                indicator.innerHTML = '← Desliza →';
                indicator.className = 'text-center text-sm text-gray-500 py-2 opacity-70';
                
                // Mostrar brevemente y luego ocultar
                container.parentNode.insertBefore(indicator, container);
                setTimeout(() => {
                    indicator.style.opacity = '0';
                    indicator.style.transition = 'opacity 0.5s';
                }, 2000);
            }
        });
        
        // Scroll vertical en columnas Kanban
        document.querySelectorAll('.kanban-column').forEach(column => {
            // Solo para táctil: añadir indicador de scroll
            if (isTouchDevice && column.scrollHeight > column.clientHeight) {
                const indicator = document.createElement('div');
                indicator.innerHTML = '<i class="fas fa-arrows-alt-v"></i>';
                indicator.className = 'absolute top-2 right-2 bg-gray-600 text-white rounded-full w-6 h-6 flex items-center justify-center opacity-70';
                
                column.style.position = 'relative';
                column.appendChild(indicator);
                
                setTimeout(() => {
                    indicator.style.opacity = '0';
                    indicator.style.transition = 'opacity 0.5s';
                }, 2000);
                
                // Mostrar brevemente al tocar la columna
                column.addEventListener('touchstart', () => {
                    indicator.style.opacity = '0.7';
                    setTimeout(() => {
                        indicator.style.opacity = '0';
                    }, 1500);
                });
            }
        });
    }
    
    // Inicializar sistemas de arrastrar y soltar en orden de prioridad
    
    // 1. Intentar con SortableJS (funciona mejor para la mayoría de dispositivos)
    try {
        if (typeof Sortable !== 'undefined') {
            console.log('Initializing SortableJS');
            initSortable();
        } else {
            console.warn('SortableJS not available, falling back to native drag & drop');
            initNativeDragDrop();
        }
    } catch (e) {
        console.error('Error initializing SortableJS:', e);
        initNativeDragDrop();
    }
    
    // 2. Añadir siempre la solución específica para táctil como respaldo
    if (isTouchDevice) {
        initTouchDragDrop();
    }
    
    // 3. Habilitar scroll por arrastre en todos los casos
    enableDragScroll();
    
    // Ajustar z-index de menús desplegables para evitar problemas
    function fixMenuZIndex() {
        const navbar = document.querySelector('nav');
        const dropdowns = document.querySelectorAll('.dropdown-menu, .dropdown-content, .submenu');
        
        if (navbar) {
            navbar.style.position = 'relative';
            navbar.style.zIndex = '1000';
        }
        
        dropdowns.forEach(dropdown => {
            dropdown.style.zIndex = '1001';
            dropdown.style.position = 'absolute';
        });
        
        const kanbanHeader = document.querySelector('.kanban-header');
        if (kanbanHeader) {
            kanbanHeader.style.zIndex = '5';
        }
    }
    
    fixMenuZIndex();
    
    console.log('Unified Kanban system initialized');
});