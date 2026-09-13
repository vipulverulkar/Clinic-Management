document.addEventListener('DOMContentLoaded', () => {
  // Multi-theme system: preset id persisted in localStorage,
  // applied as data-bs-theme + data-accent on <html>
  const THEMES = [
    { id: 'ocean-light',  name: 'Ocean Light',  icon: 'bi-sun',            bs: 'light', accent: 'blue' },
    { id: 'ocean-dark',   name: 'Ocean Dark',   icon: 'bi-moon-stars',     bs: 'dark',  accent: 'blue' },
    { id: 'teal-light',   name: 'Teal Light',   icon: 'bi-brightness-high', bs: 'light', accent: 'teal' },
    { id: 'forest-dark',  name: 'Forest Dark',  icon: 'bi-tree',           bs: 'dark',  accent: 'green' },
    { id: 'royal-dark',   name: 'Royal Dark',   icon: 'bi-gem',            bs: 'dark',  accent: 'violet' },
    { id: 'sunset-light', name: 'Sunset Light', icon: 'bi-sunset',         bs: 'light', accent: 'orange' },
    { id: 'rose-light',   name: 'Rose Light',   icon: 'bi-heart',          bs: 'light', accent: 'rose' },
    { id: 'graphite-dark', name: 'Graphite Dark', icon: 'bi-circle-half',  bs: 'dark',  accent: 'slate' },
    { id: 'cyan-dark',    name: 'Cyan Dark',    icon: 'bi-droplet',        bs: 'dark',  accent: 'cyan' },
    { id: 'mint-light',   name: 'Mint Light',   icon: 'bi-flower1',        bs: 'light', accent: 'mint' }
  ];
  const themeMenus = document.querySelectorAll('.themeMenu');
  const currentThemeId = () => {
    try { return localStorage.getItem('clinic-theme') || 'ocean-light'; }
    catch (e) { return 'ocean-light'; }
  };
  function applyTheme(id) {
    const t = THEMES.find(x => x.id === id) || THEMES[0];
    document.documentElement.setAttribute('data-bs-theme', t.bs);
    document.documentElement.setAttribute('data-accent', t.accent);
    try {
      localStorage.setItem('clinic-theme', t.id);
      localStorage.setItem('clinic-bs', t.bs);
      localStorage.setItem('clinic-accent', t.accent);
    } catch (e) {}
    themeMenus.forEach(menu => {
      menu.innerHTML = THEMES.map(x =>
        `<li><a class="dropdown-item${x.id === t.id ? ' active' : ''}" href="#" data-theme="${x.id}">` +
        `<i class="bi ${x.icon} me-2"></i>${x.name}` +
        `${x.id === t.id ? '<i class="bi bi-check-lg ms-auto"></i>' : ''}</a></li>`
      ).join('');
    });
  }
  themeMenus.forEach(menu => {
    menu.addEventListener('click', (e) => {
      const item = e.target.closest('[data-theme]');
      if (!item) return;
      e.preventDefault();
      applyTheme(item.getAttribute('data-theme'));
    });
  });
  applyTheme(currentThemeId());

  // Mobile sidebar drawer
  const sidebarToggle = document.getElementById('sidebarToggle');
  const sidebarBackdrop = document.getElementById('sidebarBackdrop');
  if (sidebarToggle) {
    sidebarToggle.addEventListener('click', () => document.body.classList.toggle('sidebar-open'));
  }
  if (sidebarBackdrop) {
    sidebarBackdrop.addEventListener('click', () => document.body.classList.remove('sidebar-open'));
  }
  document.querySelectorAll('.sidebar-link').forEach(link => {
    link.addEventListener('click', () => document.body.classList.remove('sidebar-open'));
  });

  // Highlight active nav link based on current path
  const currentPath = window.location.pathname;
  document.querySelectorAll('.sidebar-link[href], .navbar-nav .nav-link[href]').forEach(link => {
    const href = link.getAttribute('href');
    if (href === currentPath || (href !== '/dashboard' && currentPath.startsWith(href + '/'))) {
      link.classList.add('active');
    }
  });

  const tables = document.querySelectorAll('table');
  tables.forEach(table => {
    if (!table.id) return;
    const rows = table.querySelectorAll('tbody tr');
    const searchInput = document.createElement('input');
    searchInput.type = 'text';
    searchInput.className = 'form-control table-search mb-3';
    searchInput.placeholder = 'Search...';
    table.parentElement.insertBefore(searchInput, table);
    searchInput.addEventListener('input', () => {
      const term = searchInput.value.toLowerCase();
      rows.forEach(row => {
        const text = row.textContent.toLowerCase();
        row.style.display = text.includes(term) ? '' : 'none';
      });
    });
  });

  const forms = document.querySelectorAll('form');
  forms.forEach(form => {
    form.addEventListener('submit', (e) => {
      const submitBtn = form.querySelector('button[type="submit"]');
      if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Saving...';
      }
    });
  });

  const deleteForms = document.querySelectorAll('form[action*="/delete"]');
  deleteForms.forEach(form => {
    form.addEventListener('submit', (e) => {
      if (!confirm('Are you sure you want to delete this item?')) {
        e.preventDefault();
      }
    });
  });

  const datetimeInputs = document.querySelectorAll('input[type="datetime-local"]');
  datetimeInputs.forEach(input => {
    if (!input.value) {
      const now = new Date();
      now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
      input.min = now.toISOString().slice(0, 16);
    }
  });
});

function formatDate(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleDateString();
}

function formatDateTime(dateStr) {
  if (!dateStr) return '';
  return new Date(dateStr).toLocaleString();
}