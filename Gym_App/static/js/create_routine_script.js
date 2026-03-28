document.addEventListener('DOMContentLoaded', function() {
    const searchInput = document.getElementById('exercise-search');
    const resultsContainer = document.getElementById('search-results');
    const routineList = document.getElementById('routine-items-list');
    const modal = document.getElementById('exercise-modal');
    const btnNewExercise = document.getElementById('btn-new-exercise');
    const btnCloseModal = document.getElementById('close-modal');
    const asyncForm = document.getElementById('async-exercise-form');

    // Controladores de estado visual
    btnNewExercise.onclick = () => { modal.style.display = 'flex'; };
    btnCloseModal.onclick = () => { modal.style.display = 'none'; asyncForm.reset(); };

    // Event Listener para la escritura en tiempo real (Teclado)
    searchInput.addEventListener('input', function() {
        const query = this.value.trim();
        
        if (query.length > 2) {
            fetch(`/entrenamiento/api/buscar-ejercicios/?q=${encodeURIComponent(query)}`)
                .then(response => response.json())
                .then(data => {
                    resultsContainer.innerHTML = '';
                    if (data.results.length > 0) {
                        resultsContainer.style.display = 'block';
                        data.results.forEach(ex => {
                            const div = document.createElement('div');
                            div.className = 'search-item';
                            div.textContent = `${ex.name} (${ex.category})`;
                            div.onclick = () => addExerciseToRoutine(ex.id, ex.name);
                            resultsContainer.appendChild(div);
                        });
                    } else {
                        resultsContainer.style.display = 'none';
                    }
                })
                .catch(error => console.error('Error en la consulta asíncrona:', error));
        } else {
            resultsContainer.style.display = 'none';
        }
    });

    // Ocultar resultados al hacer clic fuera del área
    document.addEventListener('click', function(e) {
        if (e.target !== searchInput) resultsContainer.style.display = 'none';
    });

    // Función para inyectar el ejercicio seleccionado en el DOM
    function addExerciseToRoutine(id, name) {
        const li = document.createElement('li');
        li.style.marginBottom = '1rem';
        li.innerHTML = `
            <strong>${name}</strong>
            <input type="hidden" name="exercises[]" value="${id}">
            <input type="number" name="sets_${id}" placeholder="Series (ej. 4)" min="1" required style="width: 80px; margin-left:10px;">
            <input type="number" name="reps_${id}" placeholder="Reps (ej. 10)" min="1" required style="width: 80px; margin-left:10px;">
            <button type="button" onclick="this.parentElement.remove()" style="color: red; margin-left:10px;">X</button>
        `;
        routineList.appendChild(li);
        searchInput.value = ''; 
    }

    // Intercepción de la sumisión para ejecución asíncrona (CORREGIDO)
    asyncForm.addEventListener('submit', function(e) {
        e.preventDefault(); 
        
        const formElement = e.target;
        const targetUrl = formElement.getAttribute('data-url');
        
        if (!targetUrl) {
            console.error("Error estructural: El atributo data-url no está definido en el form.");
            return;
        }

        // Extracción del token CSRF del DOM
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
                'X-CSRFToken': csrfTokenInput.value // Inyección del token CSRF requerida por Django
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
                addExerciseToRoutine(data.id, data.name);
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