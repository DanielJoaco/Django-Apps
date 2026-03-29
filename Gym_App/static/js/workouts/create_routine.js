document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('exercise-search');
    const resultsContainer = document.getElementById('search-results');
    const routineList = document.getElementById('routine-items-list');
    const modal = document.getElementById('exercise-modal');
    const btnNewExercise = document.getElementById('btn-new-exercise');
    const btnCloseModal = document.getElementById('close-modal');
    const asyncForm = document.getElementById('async-exercise-form');
    const initialRoutineItemsScript = document.getElementById('initial-routine-items');

    // Controladores de estado visual
    btnNewExercise.onclick = () => { modal.style.display = 'flex'; };
    btnCloseModal.onclick = () => { modal.style.display = 'none'; asyncForm.reset(); };

    // Event Listener para la escritura en tiempo real (Teclado)
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length > 2) {
            // Petición asíncrona al backend
            fetch(`/workouts/api/search-exercises/?q=${encodeURIComponent(query)}`)
                .then(response => {
                    if (!response.ok) throw new Error('Error de red al buscar ejercicios');
                    return response.json();
                })
                .then(data => {
                    resultsContainer.innerHTML = ''; // Limpiar resultados anteriores
                    
                    if (data.results.length > 0) {
                        resultsContainer.style.display = 'block'; // Mostrar la caja flotante
                        
                        data.results.forEach(ex => {
                            const div = document.createElement('div');
                            div.className = 'search-item';
                            
                            const p = document.createElement('p');
                            // Formato visual: • Nombre del Ejercicio (Músculo)
                            p.textContent = `• ${ex.name} (${ex.category})`;
                            
                            div.appendChild(p);
                            
                            // Asignación de evento para agregar a la rutina
                            div.onclick = () => {
                                addExerciseToRoutine(ex.id, ex.name, ex.category);
                                resultsContainer.style.display = 'none'; // Oculta la caja al seleccionar
                            };
                            
                            resultsContainer.appendChild(div);
                        });
                    } else {
                        resultsContainer.style.display = 'none';
                    }
                })
                .catch(error => console.error('Error en la consulta asíncrona:', error));
        } else {
            // Si el usuario borra el texto y hay menos de 3 caracteres, ocultar caja
            resultsContainer.style.display = 'none';
        }
    });

    // Ocultar resultados al hacer clic fuera del área de búsqueda
    document.addEventListener('click', function(e) {
        if (e.target !== searchInput) resultsContainer.style.display = 'none';
    });

    // CORRECCIÓN: Ahora recibe la categoría/músculo para mostrarlo en el DOM
    function addExerciseToRoutine(id, name, muscleName, initialSets = '', initialReps = '') {
        const li = document.createElement('li');
        li.classList.add('routine-add-item');
        
        // Estructura semántica usando el nombre del músculo si está disponible
        const displayMuscle = muscleName ? ` <span style="color: var(--text-muted); font-size: 1.2rem;">(${muscleName})</span>` : '';
        
        li.innerHTML = `
            <div style="flex-grow: 1;">
                <strong>${name}</strong> ${displayMuscle}
                <input type="hidden" name="exercises[]" value="${id}">
            </div>
            <div>
                <input type="number" name="sets_${id}" placeholder="Series" min="1" required value="${initialSets}" style="width: 70px; margin-left:10px;" class="form-control">
                <input type="number" name="reps_${id}" placeholder="Reps" min="1" required value="${initialReps}" style="width: 70px; margin-left:10px;" class="form-control">
                <button type="button" onclick="this.parentElement.parentElement.remove()" style="color: var(--text-warning); margin-left:10px; border:none; background:none; cursor:pointer; font-weight:bold;">X</button>
            </div>
        `;
        routineList.appendChild(li);
        searchInput.value = ''; 
    }

    if (initialRoutineItemsScript) {
        try {
            const initialRoutineItems = JSON.parse(initialRoutineItemsScript.textContent);
            initialRoutineItems.forEach(item => {
                addExerciseToRoutine(item.id, item.name, item.category, item.sets, item.reps);
            });
        } catch (error) {
            console.error('Error al cargar ejercicios iniciales de la rutina:', error);
        }
    }

    // Intercepción de la sumisión para el formulario de Nuevo Ejercicio
    asyncForm.addEventListener('submit', function(e) {
        e.preventDefault(); 
        
        const formElement = e.target;
        const targetUrl = formElement.getAttribute('data-url');
        
        if (!targetUrl) {
            console.error("Error estructural: El atributo data-url no está definido en el form.");
            return;
        }

        const csrfTokenInput = document.querySelector('[name=csrfmiddlewaretoken]');
        if (!csrfTokenInput) {
            console.error("Fallo de seguridad: Token CSRF no encontrado.");
            return;
        }

        const formData = new FormData(formElement);
        
        fetch(targetUrl, {
            method: 'POST',
            body: formData,
            headers: {
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfTokenInput.value 
            }
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP Error Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            if (data.success) {
                // Al crear desde cero, pasamos 'Nuevo' temporalmente o extraemos el texto del select
                const muscleSelect = formElement.querySelector('select[name="muscle_group"]');
                const muscleText = muscleSelect ? muscleSelect.options[muscleSelect.selectedIndex].text : '';
                
                addExerciseToRoutine(data.id, data.name, muscleText);
                modal.style.display = 'none';
                formElement.reset();
            } else {
                console.error('Fallo en validación de backend:', data.errors);
                alert('Error en el formulario. Revisa los datos ingresados.');
            }
        })
        .catch(error => {
            console.error('Fallo de Red o Servidor:', error);
            alert('Error de conexión. Revisa la consola para más detalles.');
        });
    });
});