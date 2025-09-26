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
            
            // console.log('Drag started for employee:', card.getAttribute('data-employee-id'));
        });
        
        card.addEventListener('dragend', function() {
            // Asegurar que todas las clases visuales se limpien al final
            setTimeout(clearAllDragVisuals, 100);
            // console.log('Drag ended, visuals cleared');
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
            
            // console.log('Drop detected - Employee ID:', employeeId, 'Project ID:', projectId);
            
            if (!employeeId) {
                console.error('No employee ID found in drop data');
                showToast('<i class="fas fa-exclamation-triangle mr-2"></i> Error: Could not identify employee', 'error');
                return;
            }
            
            // Find the card
            const card = document.querySelector(`.employee-card[data-employee-id="${employeeId}"`);
            
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
                // console.log('Server response:', data);
                
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
            
            // console.log('Drop detected - Employee ID:', employeeId, 'Project ID:', projectId);
            
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
                // console.log('Server response:', data);
                
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
    
    // console.log('Drag and drop initialized with ' + employeeCards.length + ' employees, ' + 
    //             columns.length + ' columns, and ' + projectColumns.length + ' project columns');
    
    // Arreglar problemas de superposición con el menú desplegable
    function fixMenuZIndex() {
        // Seleccionar el menú principal y los elementos desplegables
        // Ajusta estos selectores según la estructura de tu HTML
        const navbar = document.querySelector('nav');
        const dropdowns = document.querySelectorAll('.dropdown-menu, .dropdown-content, .submenu');
        
        // Aplicar z-index alto al menú
        if (navbar) {
            navbar.style.position = 'relative';
            navbar.style.zIndex = '1000';
        }
        
        // Aplicar z-index muy alto a todos los menús desplegables
        dropdowns.forEach(dropdown => {
            dropdown.style.zIndex = '1001';
            dropdown.style.position = 'absolute';
        });
        
        // Reducir el z-index del kanban header para que no interfiera
        const kanbanHeader = document.querySelector('.kanban-header');
        if (kanbanHeader) {
            kanbanHeader.style.zIndex = '5';
            // Si es sticky, cambiarlo a relative para evitar problemas
            if (window.getComputedStyle(kanbanHeader).position === 'sticky') {
                kanbanHeader.style.position = 'relative';
            }
        }
    }
    
    // Ejecutar al cargar la página
    fixMenuZIndex();
    
    // También ejecutar cuando se haga clic en el posible activador del menú
    document.querySelectorAll('.dropdown-toggle, .navbar-toggle, .menu-toggle').forEach(toggle => {
        toggle.addEventListener('click', function(e) {
            // Pequeño retraso para asegurar que se aplica después de cualquier otro código
            setTimeout(fixMenuZIndex, 10);
        });
    });
    
    // Si el menú se muestra al hacer hover, manejar también ese caso
    document.querySelectorAll('.dropdown, .has-dropdown').forEach(dropdown => {
        dropdown.addEventListener('mouseenter', function() {
            setTimeout(fixMenuZIndex, 10);
        });
    });

    // Añadir esta función para habilitar el scroll horizontal mediante arrastre
    function enableDragToScroll(scrollContainer) {
        let isDown = false;
        let startX;
        let scrollLeft;
        let isTouchScrolling = false;
    
        // Ratón
        scrollContainer.addEventListener('mousedown', (e) => {
            if (e.target.closest('.employee-card')) return;
    
            isDown = true;
            scrollContainer.style.cursor = 'grabbing';
            startX = e.pageX - scrollContainer.offsetLeft;
            scrollLeft = scrollContainer.scrollLeft;
            e.preventDefault();
        });
    
        scrollContainer.addEventListener('mouseleave', () => {
            isDown = false;
            scrollContainer.style.cursor = 'grab';
        });
    
        scrollContainer.addEventListener('mouseup', () => {
            isDown = false;
            scrollContainer.style.cursor = 'grab';
        });
    
        scrollContainer.addEventListener('mousemove', (e) => {
            if (!isDown || document.querySelector('.employee-card.dragging')) return;
    
            const x = e.pageX - scrollContainer.offsetLeft;
            const walk = (x - startX) * 2;
            scrollContainer.scrollLeft = scrollLeft - walk;
        });
    
        // Pantalla táctil
        scrollContainer.addEventListener('touchstart', (e) => {
            if (e.target.closest('.employee-card') || e.target.closest('a') || e.target.closest('button')) return;
    
            isDown = true;
            isTouchScrolling = false;
            startX = e.touches[0].pageX - scrollContainer.offsetLeft;
            scrollLeft = scrollContainer.scrollLeft;
        }, { passive: false });
    
        scrollContainer.addEventListener('touchend', () => {
            isDown = false;
            isTouchScrolling = false;
        });
    
        scrollContainer.addEventListener('touchmove', (e) => {
            if (!isDown || document.querySelector('.employee-card.dragging')) return;
    
            const x = e.touches[0].pageX - scrollContainer.offsetLeft;
            const walk = (x - startX) * 2;
    
            if (Math.abs(walk) > 10) isTouchScrolling = true;
    
            if (isTouchScrolling) {
                scrollContainer.scrollLeft = scrollLeft - walk;
                e.preventDefault();
            }
        }, { passive: false });
    
        // Indicador táctil
        if (('ontouchstart' in window) || navigator.maxTouchPoints > 0) {
            const scrollIndicator = document.createElement('div');
            scrollIndicator.className = 'scroll-indicator';
            scrollIndicator.innerHTML = '← Desliza para ver más →';
            scrollIndicator.style.cssText = `
                position: absolute;
                bottom: 10px;
                left: 50%;
                transform: translateX(-50%);
                background-color: rgba(0,0,0,0.6);
                color: white;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 14px;
                opacity: 0.8;
                transition: opacity 0.5s ease;
                z-index: 100;
                pointer-events: none;
            `;
            scrollContainer.appendChild(scrollIndicator);
    
            setTimeout(() => { scrollIndicator.style.opacity = '0'; }, 3000);
    
            scrollContainer.addEventListener('touchstart', () => {
                scrollIndicator.style.opacity = '0.8';
                setTimeout(() => {
                    scrollIndicator.style.opacity = '0';
                }, 1500);
            });
        }
    
        scrollContainer.style.cursor = 'grab';
        // console.log('Drag-to-scroll habilitado en:', scrollContainer);
    }

    function enableTouchScrolling() {
        const columns = document.querySelectorAll('.kanban-column');
        
        columns.forEach(column => {
            // Prevenir el comportamiento de arrastrar por defecto para evitar conflictos con drag & drop
            column.addEventListener('touchstart', function(e) {
                // No interferir si estamos interactuando con una tarjeta o un elemento interactivo
                if (e.target.closest('.employee-card') || 
                    e.target.closest('a') || 
                    e.target.closest('button') || 
                    e.target.closest('input')) {
                    return;
                }
                
                // Obtener la posición inicial
                const startY = e.touches[0].clientY;
                const startScrollTop = column.scrollTop;
                let lastY = startY;
                let momentum = 0;
                let lastTimestamp = Date.now();
                
                function handleTouchMove(e) {
                    // Calcular la diferencia de posición
                    const y = e.touches[0].clientY;
                    const deltaY = lastY - y;
                    
                    // Calcular el momentum (velocidad)
                    const now = Date.now();
                    const dt = now - lastTimestamp;
                    if (dt > 0) {
                        momentum = deltaY / dt;
                    }
                    
                    // Ajustar el scroll
                    column.scrollTop += deltaY;
                    
                    // Actualizar las últimas posiciones
                    lastY = y;
                    lastTimestamp = now;
                    
                    // Evitar el scroll de página
                    if (Math.abs(deltaY) > 5) {
                        e.preventDefault();
                    }
                }
                
                function handleTouchEnd(e) {
                    // Quitar los event listeners
                    document.removeEventListener('touchmove', handleTouchMove, {passive: false});
                    document.removeEventListener('touchend', handleTouchEnd);
                    
                    // Aplicar momentum scroll para una experiencia más fluida
                    if (Math.abs(momentum) > 0.1) {
                        const momentumScroll = function() {
                            if (Math.abs(momentum) <= 0.1) return;
                            
                            column.scrollTop += momentum * 10;
                            momentum *= 0.95; // Reducir el momentum gradualmente
                            
                            requestAnimationFrame(momentumScroll);
                        };
                        
                        requestAnimationFrame(momentumScroll);
                    }
                }
                
                // Añadir los event listeners para el movimiento y fin del toque
                document.addEventListener('touchmove', handleTouchMove, {passive: false});
                document.addEventListener('touchend', handleTouchEnd);
            }, {passive: true});
            
            // Añadir indicador visual de scroll
            const addScrollIndicator = function() {
                // Verificar si el contenido necesita scroll
                if (column.scrollHeight <= column.clientHeight) return;
                
                // Crear el indicador solo si no existe
                if (!column.querySelector('.scroll-indicator')) {
                    const indicator = document.createElement('div');
                    indicator.className = 'scroll-indicator';
                    indicator.innerHTML = '<i class="fas fa-arrows-alt-v"></i>';
                    indicator.style.cssText = `
                        position: absolute;
                        top: 10px;
                        right: 10px;
                        background-color: rgba(0,0,0,0.5);
                        color: white;
                        padding: 6px;
                        border-radius: 50%;
                        width: 28px;
                        height: 28px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        opacity: 0.7;
                        transition: opacity 0.5s;
                        z-index: 10;
                        pointer-events: none;
                    `;
                    
                    // Posicionar relativamente la columna si es necesario
                    if (getComputedStyle(column).position === 'static') {
                        column.style.position = 'relative';
                    }
                    
                    column.appendChild(indicator);
                    
                    // Ocultar después de un tiempo
                    setTimeout(function() {
                        indicator.style.opacity = '0';
                    }, 3000);
                    
                    // Mostrar cuando se interactúa con la columna
                    column.addEventListener('touchstart', function() {
                        indicator.style.opacity = '0.7';
                        setTimeout(function() {
                            indicator.style.opacity = '0';
                        }, 1500);
                    });
                }
            };
            
            // Añadir el indicador de scroll
            addScrollIndicator();
            
            // Observar cambios en el contenido para actualizar el indicador
            const observer = new MutationObserver(addScrollIndicator);
            observer.observe(column, { childList: true, subtree: true });
        });
        
        // console.log('Scroll táctil habilitado en las columnas kanban');
    }
    
    // Habilitar scroll táctil
    enableTouchScrolling();
    
    
    // Ejecutar la función para habilitar el scroll por arrastre
    // Activar scroll horizontal en todos los contenedores de proyectos
    document.querySelectorAll('.projects-container').forEach(enableDragToScroll);

});