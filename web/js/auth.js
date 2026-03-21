// Auth utilities
function getAuthToken() {
  return localStorage.getItem('api_key');
}

function getUser() {
  const user = localStorage.getItem('user');
  return user ? JSON.parse(user) : null;
}

function setAuth(apiKey, user) {
  localStorage.setItem('api_key', apiKey);
  localStorage.setItem('user', JSON.stringify(user));
}

function clearAuth() {
  localStorage.removeItem('api_key');
  localStorage.removeItem('user');
}

function requireAuth() {
  if (!getAuthToken()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

function requireAdmin() {
  const user = getUser();
  if (!user || user.role !== 'admin') {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

async function apiCall(endpoint, options = {}) {
  const token = getAuthToken();
  const headers = {
    'Content-Type': 'application/json',
    ...options.headers
  };
  
  if (token) {
    headers['Authorization'] = 'Bearer ' + token;
  }
  
  try {
    const response = await fetch(`${API_URL}${endpoint}`, {
      ...options,
      headers
    });
    
    const data = await response.json();
    
    if (!response.ok) {
      if (response.status === 401 || response.status === 403) {
        clearAuth();
        window.location.href = '/login.html';
        return;
      }
      throw new Error(data.detail || data.error || data.message || 'Request failed');
    }
    
    return data;
  } catch (error) {
    throw error;
  }
}

function showError(message) {
  const errorDiv = document.createElement('div');
  errorDiv.className = 'fixed top-4 right-4 bg-red-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
  errorDiv.textContent = message;
  document.body.appendChild(errorDiv);
  
  setTimeout(() => {
    errorDiv.remove();
  }, 4000);
}

function showSuccess(message) {
  const successDiv = document.createElement('div');
  successDiv.className = 'fixed top-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50 animate-fade-in';
  successDiv.textContent = message;
  document.body.appendChild(successDiv);
  
  setTimeout(() => {
    successDiv.remove();
  }, 4000);
}
