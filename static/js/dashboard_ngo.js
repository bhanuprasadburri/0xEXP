document.addEventListener('DOMContentLoaded', () => {
  const dateEl = document.getElementById('currentDate');
  if (dateEl) {
    dateEl.textContent = new Date().toLocaleDateString('en', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
      year: 'numeric'
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

  const chartNodes = document.querySelectorAll('canvas');
  if (window.Chart && chartNodes.length) {
    new Chart(document.getElementById('activityChart'), {
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
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
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
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { y: { beginAtZero: true } }
      }
    });

    new Chart(document.getElementById('statusChart'), {
      type: 'doughnut',
      data: {
        labels: ['Available', 'Accepted', 'Completed'],
        datasets: [{
          data: [12, 8, 6],
          backgroundColor: ['#16a34a', '#22c55e', '#84cc16']
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }
});
