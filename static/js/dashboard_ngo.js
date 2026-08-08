document.addEventListener('DOMContentLoaded', () => {
  const dateEl = document.getElementById('currentDateTime');
  if (dateEl) {
    const updateClock = () => {
      const now = new Date();
      dateEl.textContent = `${now.toLocaleDateString('en', { weekday: 'short', month: 'short', day: 'numeric' })} · ${now.toLocaleTimeString('en', { hour: 'numeric', minute: '2-digit' })}`;
    };
    updateClock();
    window.setInterval(updateClock, 1000);
  }

  const themeToggle = document.getElementById('themeToggle');
  const body = document.body;
  const storedTheme = window.localStorage.getItem('ngoDashboardTheme');
  if (storedTheme === 'dark') {
    body.classList.add('dark');
  }
  if (themeToggle) {
    themeToggle.addEventListener('click', () => {
      body.classList.toggle('dark');
      const isDark = body.classList.contains('dark');
      window.localStorage.setItem('ngoDashboardTheme', isDark ? 'dark' : 'light');
    });
  }

  const dashboardShell = document.getElementById('ngoDashboardShell');
  const toggleButton = document.querySelector('.sidebar-toggle');
  if (dashboardShell && toggleButton) {
    const savedState = window.localStorage.getItem('ngoSidebarCollapsed');
    if (savedState === 'true') {
      dashboardShell.classList.add('is-collapsed');
    }

    toggleButton.addEventListener('click', () => {
      const collapsed = dashboardShell.classList.toggle('is-collapsed');
      window.localStorage.setItem('ngoSidebarCollapsed', collapsed ? 'true' : 'false');
    });
  }

  document.querySelectorAll('.action-form').forEach((form) => {
    form.addEventListener('submit', (event) => {
      if (!window.confirm('Accept this donation and move it into your active queue?')) {
        event.preventDefault();
      }
    });
  });

  const searchInput = document.getElementById('dashboardSearch');
  const donationCards = Array.from(document.querySelectorAll('#donationBoard .donation-card'));
  const categoryFilter = document.getElementById('categoryFilter');
  const cityFilter = document.getElementById('cityFilter');
  const sortFilter = document.getElementById('sortFilter');
  const paginationControls = document.getElementById('paginationControls');

  const pageSize = 4;
  let currentPage = 1;

  const applyFilters = () => {
    const searchValue = searchInput ? searchInput.value.toLowerCase() : '';
    const categoryValue = categoryFilter ? categoryFilter.value : 'all';
    const cityValue = cityFilter ? cityFilter.value : 'all';
    const sortValue = sortFilter ? sortFilter.value : 'deadline';

    const visibleCards = donationCards.filter((card) => {
      const matchesSearch = card.dataset.search.toLowerCase().includes(searchValue);
      const matchesCategory = categoryValue === 'all' || card.dataset.category === categoryValue;
      const matchesCity = cityValue === 'all' || card.dataset.city === cityValue;
      return matchesSearch && matchesCategory && matchesCity;
    });

    visibleCards.sort((a, b) => {
      if (sortValue === 'quantity') {
        return Number(b.dataset.quantity) - Number(a.dataset.quantity);
      }
      if (sortValue === 'name') {
        return a.dataset.search.localeCompare(b.dataset.search);
      }
      return new Date(a.dataset.deadline || 0) - new Date(b.dataset.deadline || 0);
    });

    donationCards.forEach((card) => card.style.display = 'none');
    visibleCards.forEach((card) => card.style.display = 'grid');

    const totalPages = Math.max(1, Math.ceil(visibleCards.length / pageSize));
    currentPage = Math.min(currentPage, totalPages);
    const startIndex = (currentPage - 1) * pageSize;
    const endIndex = startIndex + pageSize;

    donationCards.forEach((card) => {
      const visible = visibleCards.includes(card) && visibleCards.indexOf(card) >= startIndex && visibleCards.indexOf(card) < endIndex;
      card.style.display = visible ? 'grid' : 'none';
    });

    if (paginationControls) {
      paginationControls.innerHTML = '';
      for (let index = 1; index <= totalPages; index += 1) {
        const button = document.createElement('button');
        button.type = 'button';
        button.textContent = index;
        button.className = index === currentPage ? 'active' : '';
        button.addEventListener('click', () => {
          currentPage = index;
          applyFilters();
        });
        paginationControls.appendChild(button);
      }
    }
  };

  [searchInput, categoryFilter, cityFilter, sortFilter].forEach((element) => {
    if (element) {
      element.addEventListener('input', applyFilters);
      element.addEventListener('change', applyFilters);
    }
  });

  if (donationCards.length) {
    applyFilters();
  }

  const chartNodes = document.querySelectorAll('canvas');
  if (window.Chart && chartNodes.length) {
    new Chart(document.getElementById('monthlyDonationsChart'), {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Donations',
          data: [8, 12, 10, 16, 14, 18],
          borderColor: '#16a34a',
          backgroundColor: 'rgba(22, 163, 74, 0.16)',
          fill: true,
          tension: 0.35
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });

    new Chart(document.getElementById('mealsChart'), {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{
          label: 'Meals distributed',
          data: [520, 680, 610, 760, 740, 900],
          backgroundColor: ['#16a34a', '#22c55e', '#16a34a', '#22c55e', '#16a34a', '#84cc16']
        }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });

    new Chart(document.getElementById('categoriesChart'), {
      type: 'doughnut',
      data: {
        labels: ['Produce', 'Cooked', 'Bakery', 'Packaged'],
        datasets: [{ data: [35, 25, 20, 20], backgroundColor: ['#16a34a', '#22c55e', '#84cc16', '#4ade80'] }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' } } }
    });

    new Chart(document.getElementById('successRateChart'), {
      type: 'radar',
      data: {
        labels: ['Pickup', 'Routing', 'Distribution', 'Follow-up'],
        datasets: [{ label: 'Success', data: [90, 88, 93, 86], backgroundColor: 'rgba(22, 163, 74, 0.14)', borderColor: '#16a34a' }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } } }
    });

    new Chart(document.getElementById('wasteChart'), {
      type: 'bar',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{ label: 'Waste reduced', data: [18, 22, 24, 27, 30, 33], backgroundColor: '#4ade80' }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });

    new Chart(document.getElementById('familiesChart'), {
      type: 'line',
      data: {
        labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
        datasets: [{ label: 'Families helped', data: [24, 32, 28, 41, 47, 55], borderColor: '#84cc16', backgroundColor: 'rgba(132, 204, 22, 0.16)', fill: true, tension: 0.3 }]
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });
  }
});
