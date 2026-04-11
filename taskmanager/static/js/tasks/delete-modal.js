const deleteModal = document.getElementById('deleteModal');
const deleteTaskForm = document.getElementById('deleteTaskForm');

function openDeleteModal(deleteUrl) {
	if (!deleteModal || !deleteTaskForm) {
		return;
	}

	deleteTaskForm.action = deleteUrl;
	deleteModal.classList.add('is-open');
	deleteModal.setAttribute('aria-hidden', 'false');
}

function closeDeleteModal() {
	if (!deleteModal || !deleteTaskForm) {
		return;
	}

	deleteTaskForm.removeAttribute('action');
	deleteModal.classList.remove('is-open');
	deleteModal.setAttribute('aria-hidden', 'true');
}

window.openDeleteModal = openDeleteModal;
window.closeDeleteModal = closeDeleteModal;

if (deleteModal) {
	deleteModal.addEventListener('click', function (event) {
		if (event.target === deleteModal) {
			closeDeleteModal();
		}
	});
}
