document.addEventListener('DOMContentLoaded', () => {
  const globalSearch = document.getElementById('globalSearch');
  const dashboardPage = document.getElementById('dashboardPage');
  const sidebar = document.getElementById('donorSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleButton = document.getElementById('sidebarToggle');
  const notificationsButton = document.getElementById('notificationsButton');
  const notificationsMenu = document.getElementById('notificationsMenu');
  const profileButton = document.getElementById('profileButton');
  const profileMenu = document.getElementById('profileMenu');
  const mobileMenuButton = document.getElementById('mobileMenuButton');
  const mobileMenuPanel = document.getElementById('mobileMenuPanel');
  const mobileNavBackdrop = document.getElementById('mobileNavBackdrop');
  const closeMobileMenuButton = document.getElementById('closeMobileMenu');

  if (window.lucide) { window.lucide.createIcons(); }

  const applyTheme = (theme) => {
    const isDark = theme === 'dark';
    document.documentElement.classList.toggle('dark', isDark);
    document.body.classList.toggle('dark', isDark);
    if (window.lucide) { window.lucide.createIcons(); }
  };

  const storedTheme = localStorage.getItem('0xexp-theme') || 'light';
  applyTheme(storedTheme);

  const updateMenuState = () => {
    if (window.innerWidth > 900 && sidebar) {
      sidebar.setAttribute('data-mobile-open', 'false');
      closeMobilePanel();
    }
  };

  const closeMenu = (menu) => {
    if (menu) { menu.removeAttribute('data-open'); }
  };

  const closeMobilePanel = () => {
    if (mobileMenuPanel) { mobileMenuPanel.classList.remove('open'); }
    if (mobileNavBackdrop) { mobileNavBackdrop.style.display = 'none'; }
    if (mobileMenuButton) { mobileMenuButton.setAttribute('aria-expanded', 'false'); }
  };

  const closeAllMenus = () => {
    [notificationsMenu, profileMenu].forEach((menu) => closeMenu(menu));
    [notificationsButton, profileButton].forEach((button) => {
      if (button) { button.setAttribute('aria-expanded', 'false'); }
    });
    closeMobilePanel();
  };

  const toggleMenu = (button, menu) => {
    const isOpen = button?.getAttribute('aria-expanded') === 'true';
    closeAllMenus();
    if (!isOpen) {
      menu.setAttribute('data-open', 'true');
      button.setAttribute('aria-expanded', 'true');
    }
  };

  if (notificationsButton && notificationsMenu) {
    notificationsButton.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleMenu(notificationsButton, notificationsMenu);
    });
  }

  if (profileButton && profileMenu) {
    profileButton.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleMenu(profileButton, profileMenu);
    });
  }

  if (mobileMenuButton && mobileMenuPanel && mobileNavBackdrop) {
    mobileMenuButton.addEventListener('click', (event) => {
      event.stopPropagation();
      const isOpen = mobileMenuButton.getAttribute('aria-expanded') === 'true';
      closeAllMenus();
      if (!isOpen) {
        mobileNavBackdrop.style.display = 'block';
        mobileMenuPanel.classList.add('open');
        mobileMenuButton.setAttribute('aria-expanded', 'true');
      }
    });
  }

  if (closeMobileMenuButton) { closeMobileMenuButton.addEventListener('click', closeMobilePanel); }
  if (mobileNavBackdrop) { mobileNavBackdrop.addEventListener('click', closeMobilePanel); }

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.navbar-menu') && !event.target.closest('#notificationsButton') && !event.target.closest('#profileButton') && !event.target.closest('#mobileMenuButton')) {
      closeAllMenus();
    }
  });

  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      globalSearch?.focus();
      globalSearch?.select();
    }
    if (event.key === 'Escape') { closeAllMenus(); }
  });

  if (toggleButton) {
    toggleButton.addEventListener('click', () => {
      if (sidebar) {
        sidebar.classList.toggle('is-collapsed');
      }
    });
  }

  if (overlay) {
    overlay.addEventListener('click', () => {
      if (sidebar) { sidebar.classList.remove('is-collapsed'); }
    });
  }

  const restoreViewportState = () => {
    const storedScroll = sessionStorage.getItem('donor-dashboard-scroll');
    if (storedScroll) {
      window.scrollTo(0, Number(storedScroll));
    }
    if (dashboardPage) {
      dashboardPage.style.minHeight = '100vh';
      dashboardPage.style.overflow = 'visible';
    }
  };

  const saveViewportState = () => {
    sessionStorage.setItem('donor-dashboard-scroll', String(window.scrollY || 0));
  };

  window.addEventListener('scroll', saveViewportState, { passive: true });
  window.addEventListener('pageshow', restoreViewportState);
  window.addEventListener('visibilitychange', () => {
    if (document.visibilityState === 'visible') { restoreViewportState(); }
  });
  window.addEventListener('resize', updateMenuState);
  restoreViewportState();

  document.querySelectorAll('[data-target]').forEach((node) => {
    const target = Number(node.getAttribute('data-target')) || 0;
    let current = 0;
    const step = Math.max(1, Math.round(target / 18));
    const timer = window.setInterval(() => {
      current += step;
      if (current >= target) {
        current = target;
        window.clearInterval(timer);
      }
      node.textContent = current.toLocaleString();
    }, 35);
  });

  document.querySelectorAll('.sparkline .sparkbar').forEach((bar) => {
    const height = bar.getAttribute('data-height');
    if (height) {
      bar.style.height = `${height}%`;
    }
  });

  document.querySelectorAll('.progress-fill').forEach((bar) => {
    const width = bar.getAttribute('data-progress');
    if (width) {
      bar.style.width = `${width}%`;
    }
  });

  document.querySelectorAll('.action-card, .stat-card, .donation-card, .panel-card').forEach((card) => {
    card.classList.add('is-ready');
  });

  const monthlyCanvas = document.getElementById('monthlyChart');
  const categoryCanvas = document.getElementById('categoryChart');

  const monthlyLabels = JSON.parse(document.getElementById('monthlyChartData').textContent || '[]');
  const monthlyValues = JSON.parse(document.getElementById('monthlyChartValues').textContent || '[]');
  const categoryLabels = JSON.parse(document.getElementById('categoryChartData').textContent || '[]');
  const categoryValues = JSON.parse(document.getElementById('categoryChartValues').textContent || '[]');

  if (monthlyCanvas && window.Chart) {
    new window.Chart(monthlyCanvas, {
      type: 'line',
      data: {
        labels: monthlyLabels,
        datasets: [{
          label: 'Donations',
          data: monthlyValues,
          borderColor: '#16a34a',
          backgroundColor: 'rgba(22, 163, 74, 0.14)',
          tension: 0.35,
          fill: true,
          pointRadius: 3,
          pointHoverRadius: 4,
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true, ticks: { color: '#64748b' } }, x: { ticks: { color: '#64748b' } } }
      }
    });
  }

  if (categoryCanvas && window.Chart) {
    new window.Chart(categoryCanvas, {
      type: 'doughnut',
      data: {
        labels: categoryLabels,
        datasets: [{
          data: categoryValues,
          backgroundColor: ['#16a34a', '#22c55e', '#84cc16', '#4ade80', '#a3e635', '#bef264'],
          borderWidth: 0,
        }]
      },
      options: { responsive: true, plugins: { legend: { position: 'bottom' } } }
    });
  }
});
