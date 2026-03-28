 function openModal(modalId) {
            document.getElementById(modalId).style.display = 'flex';
            // Bloquea el scroll del fondo cuando el modal está abierto
            document.body.style.overflow = 'hidden'; 
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
            // Restaura el scroll
            document.body.style.overflow = 'auto'; 
        }

        // Cierra el modal si el usuario hace clic en el fondo oscuro (fuera del contenido)
        window.onclick = function(event) {
            if (event.target.classList.contains('custom-modal')) {
                event.target.style.display = 'none';
                document.body.style.overflow = 'auto';
            }
        }