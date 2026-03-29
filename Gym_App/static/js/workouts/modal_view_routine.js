 function openModal(modalId) {
            document.getElementById(modalId).style.display = 'flex';
            // Bloquea el scroll del fondo cuando el modal está abierto
            document.body.style.overflow = 'hidden'; 
        }

        const deleteCountdownTimers = {};

        function openDeleteConfirmModal(confirmModalId, detailModalId) {
            if (detailModalId) {
                closeModal(detailModalId);
            }

            const confirmModal = document.getElementById(confirmModalId);
            if (!confirmModal) {
                return;
            }

            confirmModal.style.display = 'flex';
            document.body.style.overflow = 'hidden';

            const yesButton = confirmModal.querySelector('.confirm-yes-button');
            if (!yesButton) {
                return;
            }

            if (deleteCountdownTimers[confirmModalId]) {
                clearInterval(deleteCountdownTimers[confirmModalId]);
            }

            let remainingSeconds = 3;
            yesButton.disabled = true;
            yesButton.textContent = `Si (${remainingSeconds})`;

            deleteCountdownTimers[confirmModalId] = setInterval(() => {
                remainingSeconds -= 1;

                if (remainingSeconds > 0) {
                    yesButton.textContent = `Si (${remainingSeconds})`;
                    return;
                }

                clearInterval(deleteCountdownTimers[confirmModalId]);
                deleteCountdownTimers[confirmModalId] = null;
                yesButton.disabled = false;
                yesButton.textContent = 'Si';
            }, 1000);
        }

        function closeModal(modalId) {
            document.getElementById(modalId).style.display = 'none';
            // Restaura el scroll
            document.body.style.overflow = 'auto'; 
        }

        function closeDeleteConfirmModal(confirmModalId) {
            const confirmModal = document.getElementById(confirmModalId);
            if (!confirmModal) {
                return;
            }

            confirmModal.style.display = 'none';

            if (deleteCountdownTimers[confirmModalId]) {
                clearInterval(deleteCountdownTimers[confirmModalId]);
                deleteCountdownTimers[confirmModalId] = null;
            }

            document.body.style.overflow = 'auto';
        }

        function confirmDeleteRoutine(buttonElement) {
            if (buttonElement.disabled) {
                return;
            }

            const deleteUrl = buttonElement.dataset.deleteUrl;
            if (deleteUrl) {
                window.location.href = deleteUrl;
            }
        }

        // Cierra el modal si el usuario hace clic en el fondo oscuro (fuera del contenido)
        window.onclick = function(event) {
            if (event.target.classList.contains('custom-modal')) {
                event.target.style.display = 'none';
                const modalId = event.target.id;
                if (deleteCountdownTimers[modalId]) {
                    clearInterval(deleteCountdownTimers[modalId]);
                    deleteCountdownTimers[modalId] = null;
                }
                document.body.style.overflow = 'auto';
            }
        }