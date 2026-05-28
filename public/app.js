const Auth = {
  getToken: () => localStorage.getItem('slideai_token'),
  setToken: (t) => localStorage.setItem('slideai_token', t),
  clearToken: () => localStorage.removeItem('slideai_token'),
  isLoggedIn: () => !!localStorage.getItem('slideai_token'),
};

async function apiFetch(path, options = {}) {
  const token = Auth.getToken();
  const isFormData = options.body instanceof FormData;
  const headers = isFormData ? {} : { 'Content-Type': 'application/json' };
  Object.assign(headers, options.headers || {});
  if (token) headers['Authorization'] = `Bearer ${token}`;
  const res = await fetch(path, { ...options, headers });
  if (res.status === 401) {
    Auth.clearToken();
    window.location.href = '/auth.html';
    return;
  }
  return res;
}

function requireAuth() {
  if (!Auth.isLoggedIn()) window.location.href = '/auth.html';
}

function redirectIfLoggedIn() {
  if (Auth.isLoggedIn()) window.location.href = '/dashboard.html';
}

function showToast(message, type = 'info') {
  let container = document.getElementById('toast-container');
  if (!container) {
    container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container';
    document.body.appendChild(container);
  }
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message;
  container.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}

function getParam(name) {
  return new URLSearchParams(window.location.search).get(name);
}

function esc(str) {
  const d = document.createElement('div');
  d.textContent = str ?? '';
  return d.innerHTML;
}
