document.addEventListener('DOMContentLoaded', () => {
	const currentPath = window.location.pathname.toLowerCase();
	const normalizedPath = currentPath.length > 1 ? currentPath.replace(/\/+$/, '') : currentPath;

	const navMap = [
		{ id: 'dashboard-link', prefixes: ['/dashboard'] },
		{ id: 'routines-link', prefixes: ['/workouts/routines'] },
		{ id: 'records-link', prefixes: ['/workouts/records'] },
		{ id: 'weight-link', prefixes: ['/measurements', '/weight'] }
	];

	navMap.forEach(({ id, prefixes }) => {
		const link = document.getElementById(id);
		if (!link) {
			return;
		}

		const isDashboardRoot = id === 'dashboard-link' && normalizedPath === '/';
		const isActive = isDashboardRoot || prefixes.some(prefix => normalizedPath.startsWith(prefix));
		if (isActive) {
			link.classList.add('nav-link-active');
			link.setAttribute('aria-current', 'page');
		}
	});
});
