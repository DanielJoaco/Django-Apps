document.addEventListener('DOMContentLoaded', () => {
	const currentPath = window.location.pathname.toLowerCase();
	const normalizedPath = currentPath.length > 1 ? currentPath.replace(/\/+$/, '') : currentPath;
	const mobileMenuWrapper = document.getElementById('mobile-menu-wrapper');
	const mobileMenuToggle = document.getElementById('mobile-menu-toggle');
	const mobileNavList = document.getElementById('mobile-nav-list');
	const submenuLinks = document.querySelectorAll('.nav-item-with-submenu .nav-item-row > a[data-submenu]');
	const submenuItems = document.querySelectorAll('.nav-item-with-submenu');
	const logoTitle = document.getElementById('logo-title');
	const logoTitleMobile = document.getElementById('logo-title-mobile');
	const isTouchMode = window.matchMedia('(hover: none)').matches;

	if (logoTitle && logoTitleMobile) {
		logoTitle.textContent = logoTitleMobile.textContent.trim() || 'Gym App';
	}

	const navMap = [
		{ ids: ['dashboard-link', 'dashboard-link-mobile'], prefixes: ['/dashboard'] },
		{ ids: ['routines-link', 'routines-link-mobile'], prefixes: ['/workouts/routines'] },
		{ ids: ['records-link', 'records-link-mobile'], prefixes: ['/workouts/records'] },
		{ ids: ['weight-link', 'weight-link-mobile'], prefixes: ['/measurements', '/weight'] }
	];

	navMap.forEach(({ ids, prefixes }) => {
		const isDashboardRoot = normalizedPath === '/';
		const isActive = isDashboardRoot
			? ids.includes('dashboard-link')
			: prefixes.some(prefix => normalizedPath.startsWith(prefix));

		if (!isActive) {
			return;
		}

		ids.forEach((id) => {
			const link = document.getElementById(id);
			if (!link) {
				return;
			}

			link.classList.add('nav-link-active');
			link.setAttribute('aria-current', 'page');
		});
	});

	const closeAllSubmenus = () => {
		submenuItems.forEach((item) => {
			const triggerLink = item.querySelector('.nav-item-row > a[data-submenu]');
			const submenu = item.querySelector('.nav-submenu');
			item.classList.remove('is-open');
			if (triggerLink) {
				triggerLink.setAttribute('aria-expanded', 'false');
			}
			if (submenu) {
				submenu.setAttribute('aria-hidden', 'true');
			}
		});
	};

	const closeMobileMenu = () => {
		if (!mobileMenuWrapper || !mobileMenuToggle || !mobileNavList) {
			return;
		}

		mobileMenuWrapper.classList.remove('is-open');
		mobileMenuToggle.setAttribute('aria-expanded', 'false');
		mobileNavList.setAttribute('aria-hidden', 'true');
		closeAllSubmenus();
	};

	submenuLinks.forEach((link) => {
		link.addEventListener('click', (event) => {
			if (!isTouchMode) {
				return;
			}

			event.preventDefault();
			event.stopPropagation();
			const parent = link.closest('.nav-item-with-submenu');
			const submenu = parent?.querySelector('.nav-submenu');
			if (!parent || !submenu) {
				return;
			}

			const shouldOpen = !parent.classList.contains('is-open');
			if (!shouldOpen) {
				window.location.href = link.href;
				return;
			}

			closeAllSubmenus();
			parent.classList.add('is-open');
			link.setAttribute('aria-expanded', 'true');
			submenu.setAttribute('aria-hidden', 'false');
		});
	});

	mobileMenuToggle?.addEventListener('click', (event) => {
		event.stopPropagation();
		if (!mobileMenuWrapper || !mobileNavList) {
			return;
		}

		const isOpen = mobileMenuWrapper.classList.toggle('is-open');
		mobileMenuToggle.setAttribute('aria-expanded', isOpen ? 'true' : 'false');
		mobileNavList.setAttribute('aria-hidden', isOpen ? 'false' : 'true');
	});

	document.addEventListener('click', (event) => {
		if (!mobileMenuWrapper || !mobileMenuWrapper.contains(event.target)) {
			closeMobileMenu();
			closeAllSubmenus();
		}
	});

	mobileNavList?.querySelectorAll('a').forEach((link) => {
		link.addEventListener('click', () => {
			closeMobileMenu();
		});
	});
});
