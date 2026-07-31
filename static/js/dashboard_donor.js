document.addEventListener('DOMContentLoaded', () => {
  const globalSearch = document.getElementById('globalSearch');
  const dashboardPage = document.getElementById('dashboardPage');
  const sidebar = document.getElementById('donorSidebar');
  const overlay = document.getElementById('sidebarOverlay');
  const toggleButton = document.getElementById('sidebarToggle');
  const themeToggle = document.getElementById('themeToggle');
  const mobileThemeToggle = document.getElementById('mobileThemeToggle');
  const notificationsButton = document.getElementById('notificationsButton');
  const notificationsMenu = document.getElementById('notificationsMenu');
  const messagesButton = document.getElementById('messagesButton');
  const messagesMenu = document.getElementById('messagesMenu');
  const profileButton = document.getElementById('profileButton');
  const profileMenu = document.getElementById('profileMenu');
  const mobileMenuButton = document.getElementById('mobileMenuButton');
  const mobileMenuPanel = document.getElementById('mobileMenuPanel');
  const mobileNavBackdrop = document.getElementById('mobileNavBackdrop');
  const closeMobileMenuButton = document.getElementById('closeMobileMenu');

  if (window.lucide) {
    window.lucide.createIcons();
  }

  const applyTheme = (theme) => {
    const isDark = theme === 'dark';
    document.documentElement.classList.toggle('dark', isDark);
    document.body.classList.toggle('dark', isDark);
    [themeToggle, mobileThemeToggle].forEach((button) => {
      if (button) {
        button.setAttribute('aria-pressed', String(isDark));
        const icon = button.querySelector('i');
        if (icon) {
          icon.setAttribute('data-lucide', isDark ? 'sun' : 'moon');
        }
      }
    });
    if (window.lucide) {
      window.lucide.createIcons();
    }
  };

  const storedTheme = localStorage.getItem('0xexp-theme') || 'light';
  applyTheme(storedTheme);

  const toggleTheme = () => {
    const nextTheme = document.documentElement.classList.contains('dark') ? 'light' : 'dark';
    localStorage.setItem('0xexp-theme', nextTheme);
    applyTheme(nextTheme);
  };

  if (themeToggle) {
    themeToggle.addEventListener('click', toggleTheme);
  }
  if (mobileThemeToggle) {
    mobileThemeToggle.addEventListener('click', toggleTheme);
  }

  const updateMenuState = () => {
    const isMobile = window.innerWidth <= 900;
    if (!isMobile && sidebar) {
      sidebar.setAttribute('data-mobile-open', 'false');
    }
    if (!isMobile) {
      closeMobilePanel();
    }
  };

  const closeMenu = (menu) => {
    if (menu) {
      menu.removeAttribute('data-open');
    }
  };

  const closeMobilePanel = () => {
    if (mobileMenuPanel) {
      mobileMenuPanel.classList.remove('open');
    }
    if (mobileNavBackdrop) {
      mobileNavBackdrop.style.display = 'none';
    }
    if (mobileMenuButton) {
      mobileMenuButton.setAttribute('aria-expanded', 'false');
    }
  };

  const closeAllMenus = () => {
    [notificationsMenu, messagesMenu, profileMenu].forEach((menu) => closeMenu(menu));
    [notificationsButton, messagesButton, profileButton].forEach((button) => {
      if (button) {
        button.setAttribute('aria-expanded', 'false');
      }
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

  if (messagesButton && messagesMenu) {
    messagesButton.addEventListener('click', (event) => {
      event.stopPropagation();
      toggleMenu(messagesButton, messagesMenu);
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

  if (closeMobileMenuButton) {
    closeMobileMenuButton.addEventListener('click', closeMobilePanel);
  }

  if (mobileNavBackdrop) {
    mobileNavBackdrop.addEventListener('click', closeMobilePanel);
  }

  document.addEventListener('click', (event) => {
    if (!event.target.closest('.navbar-menu') && !event.target.closest('#notificationsButton') && !event.target.closest('#messagesButton') && !event.target.closest('#profileButton') && !event.target.closest('#mobileMenuButton')) {
      closeAllMenus();
    }
  });

  document.addEventListener('keydown', (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 'k') {
      event.preventDefault();
      globalSearch?.focus();
      globalSearch?.select();
    }
    if (event.key === 'Escape') {
      closeAllMenus();
    }
  });

  const openMobileSidebar = () => {
    if (sidebar) {
      sidebar.setAttribute('data-mobile-open', 'true');
    }
    if (overlay) {
      overlay.classList.add('active');
    }
  };

  const closeMobileSidebar = () => {
    if (sidebar) {
      sidebar.setAttribute('data-mobile-open', 'false');
    }
    if (overlay) {
      overlay.classList.remove('active');
    }
  };

  if (toggleButton) {
    toggleButton.addEventListener('click', () => {
      if (window.innerWidth <= 900) {
        const isOpen = sidebar?.getAttribute('data-mobile-open') === 'true';
        if (isOpen) {
          closeMobileSidebar();
        } else {
          openMobileSidebar();
        }
      }
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
    if (document.visibilityState === 'visible') {
      restoreViewportState();
    }
  });
  window.addEventListener('resize', () => {
    restoreViewportState();
  });
  restoreViewportState();

  if (overlay) {
    overlay.addEventListener('click', closeMobileSidebar);
  }

  window.addEventListener('resize', updateMenuState);
  updateMenuState();

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
    }, 40);
  });

  document.querySelectorAll('.sparkline .sparkbar').forEach((bar) => {
    const height = bar.getAttribute('data-height');
    if (height) {
      bar.style.height = `${height}%`;
    }
  });

  document.querySelectorAll('.btn-ripple').forEach((button) => {
    button.addEventListener('click', (event) => {
      const ripple = document.createElement('span');
      ripple.className = 'ripple';
      const rect = button.getBoundingClientRect();
      const size = Math.max(rect.width, rect.height);
      ripple.style.width = `${size}px`;
      ripple.style.height = `${size}px`;
      ripple.style.left = `${event.clientX - rect.left}px`;
      ripple.style.top = `${event.clientY - rect.top}px`;
      button.appendChild(ripple);
      window.setTimeout(() => ripple.remove(), 500);
    });
  });

  const chartCanvas = document.getElementById('donationChart');
  if (chartCanvas && window.Chart) {
    const chart = new Chart(chartCanvas, {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul'],
        datasets: [{
          label: 'Meals donated',
          data: [12, 18, 24, 29, 35, 41, 48],
          borderColor: '#16a34a',
          backgroundColor: 'rgba(22, 163, 74, 0.18)',
          fill: true,
          tension: 0.34,
          pointRadius: 3,
          pointHoverRadius: 5,
          pointBackgroundColor: '#ffffff',
          pointBorderColor: '#16a34a',
          borderWidth: 2,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false }
        },
        scales: {
          x: {
            grid: { display: false },
            ticks: { color: '#6b7280' }
          },
          y: {
            beginAtZero: true,
            grid: { color: 'rgba(148, 163, 184, 0.16)' },
            ticks: { color: '#6b7280' }
          }
        }
      }
    });
  }
});
