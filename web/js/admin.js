// Admin panel logic
let currentTab = 'users';
let masterKey = null;

// Helper to escape HTML and prevent XSS
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

const BANKS = [
  { name: 'MB Bank', code: '970422' },
  { name: 'Vietcombank', code: '970436' },
  { name: 'Techcombank', code: '970407' },
  { name: 'ACB', code: '970416' },
  { name: 'BIDV', code: '970418' },
  { name: 'VPBank', code: '970432' },
  { name: 'TPBank', code: '970423' },
  { name: 'Sacombank', code: '970403' },
  { name: 'HDBank', code: '970437' },
  { name: 'VIB', code: '970441' },
  { name: 'MSB', code: '970426' },
  { name: 'SHB', code: '970443' },
  { name: 'Eximbank', code: '970431' },
  { name: 'OCB', code: '970448' },
  { name: 'LienVietPostBank', code: '970449' },
  { name: 'ABBank', code: '970423' },
  { name: 'Nam A Bank', code: '970428' },
  { name: 'SCB', code: '970429' },
  { name: 'Bac A Bank', code: '970409' },
  { name: 'CAKE', code: '546034' },
  { name: 'Ubank', code: '546035' }
];

document.addEventListener('DOMContentLoaded', () => {
  // Check if already logged in
  masterKey = localStorage.getItem('admin_key');
  
  if (masterKey) {
    showAdminPanel();
  } else {
    showLoginScreen();
  }
});

function showLoginScreen() {
  document.getElementById('loginScreen').classList.remove('hidden');
  document.getElementById('adminPanel').classList.add('hidden');
  
  document.getElementById('loginForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const key = document.getElementById('masterKey').value.trim();
    const errorDiv = document.getElementById('loginError');
    
    try {
      // Verify master key
      const response = await fetch(`${API_URL}/v1/admin/verify`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': 'Bearer ' + key
        }
      });
      
      if (!response.ok) {
        throw new Error('Invalid master key');
      }
      
      masterKey = key;
      localStorage.setItem('admin_key', key);
      
      showAdminPanel();
      
    } catch (error) {
      errorDiv.textContent = error.message;
      errorDiv.classList.remove('hidden');
    }
  });
}

function showAdminPanel() {
  document.getElementById('loginScreen').classList.add('hidden');
  document.getElementById('adminPanel').classList.remove('hidden');
  
  // Setup tabs
  document.querySelectorAll('[data-tab]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const tab = e.target.getAttribute('data-tab');
      switchTab(tab);
    });
  });
  
  // Logout
  document.getElementById('adminLogout').addEventListener('click', () => {
    localStorage.removeItem('admin_key');
    masterKey = null;
    showLoginScreen();
  });
  
  // Load initial tab
  loadUsers();
}

function switchTab(tab) {
  currentTab = tab;
  
  // Update tab buttons
  document.querySelectorAll('[data-tab]').forEach(btn => {
    if (btn.getAttribute('data-tab') === tab) {
      btn.classList.add('bg-indigo-600');
      btn.classList.remove('bg-gray-800');
    } else {
      btn.classList.remove('bg-indigo-600');
      btn.classList.add('bg-gray-800');
    }
  });
  
  // Hide all tabs
  document.querySelectorAll('[data-tab-content]').forEach(el => {
    el.classList.add('hidden');
  });
  
  // Show selected tab
  document.getElementById(`${tab}Tab`).classList.remove('hidden');
  
  // Load data
  switch(tab) {
    case 'users':
      loadUsers();
      break;
    case 'apikeys':
      loadAllApiKeys();
      break;
    case 'payments':
      loadPayments();
      break;
    case 'usage':
      loadAdminUsage();
      break;
    case 'settings':
      loadSettings();
      break;
  }
}

async function adminApiCall(endpoint, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': 'Bearer ' + masterKey,
    ...options.headers
  };
  
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers
  });
  
  const data = await response.json();
  
  if (!response.ok) {
    throw new Error(data.error || data.message || 'Request failed');
  }
  
  return data;
}

// Users Tab
async function loadUsers() {
  try {
    const users = await adminApiCall('/v1/admin/users');
    
    const tbody = document.getElementById('usersTable');
    tbody.innerHTML = '';
    
    users.forEach(user => {
      const tr = document.createElement('tr');
      
      // Cell 1: User name (XSS risk!)
      const tdName = document.createElement('td');
      tdName.textContent = user.name;
      tr.appendChild(tdName);
      
      // Cell 2: Email (XSS risk!)
      const tdEmail = document.createElement('td');
      tdEmail.textContent = user.email;
      tr.appendChild(tdEmail);
      
      // Cell 3: Plan badge
      const tdPlan = document.createElement('td');
      tdPlan.innerHTML = `<span class="plan-badge plan-${escapeHtml(user.plan)}">${escapeHtml(user.plan)}</span>`;
      tr.appendChild(tdPlan);
      
      // Cell 4: Created date
      const tdDate = document.createElement('td');
      tdDate.textContent = new Date(user.created_at).toLocaleDateString();
      tr.appendChild(tdDate);
      
      // Cell 5: Total requests
      const tdRequests = document.createElement('td');
      tdRequests.textContent = user.total_requests || 0;
      tr.appendChild(tdRequests);
      
      // Cell 6: Actions
      const tdActions = document.createElement('td');
      const btnView = document.createElement('button');
      btnView.className = 'text-indigo-500 hover:text-indigo-400 text-sm';
      btnView.textContent = 'View';
      btnView.onclick = () => viewUser(user.id);
      tdActions.appendChild(btnView);
      tr.appendChild(tdActions);
      
      tbody.appendChild(tr);
    });
    
  } catch (error) {
    console.error('Failed to load users:', error);
  }
}

function searchUsers() {
  const query = document.getElementById('userSearch').value.toLowerCase();
  const rows = document.querySelectorAll('#usersTable tr');
  
  rows.forEach(row => {
    const text = row.textContent.toLowerCase();
    row.style.display = text.includes(query) ? '' : 'none';
  });
}

function viewUser(userId) {
  // Could open a modal with user details
  alert(`View user: ${userId}`);
}

// API Keys Tab
async function loadAllApiKeys() {
  try {
    const keys = await adminApiCall('/v1/admin/keys');
    
    const tbody = document.getElementById('allKeysTable');
    tbody.innerHTML = '';
    
    keys.forEach(key => {
      const tr = document.createElement('tr');
      
      // Cell 1: Truncated key
      const tdKey = document.createElement('td');
      tdKey.className = 'font-mono text-sm';
      tdKey.textContent = key.key.substring(0, 16) + '...';
      tr.appendChild(tdKey);
      
      // Cell 2: User email (XSS risk!)
      const tdEmail = document.createElement('td');
      tdEmail.textContent = key.user_email;
      tr.appendChild(tdEmail);
      
      // Cell 3: Plan badge
      const tdPlan = document.createElement('td');
      tdPlan.innerHTML = `<span class="plan-badge plan-${escapeHtml(key.plan)}">${escapeHtml(key.plan)}</span>`;
      tr.appendChild(tdPlan);
      
      // Cell 4: Total requests
      const tdRequests = document.createElement('td');
      tdRequests.textContent = key.total_requests || 0;
      tr.appendChild(tdRequests);
      
      // Cell 5: Toggle button
      const tdActions = document.createElement('td');
      const btnToggle = document.createElement('button');
      btnToggle.className = `px-3 py-1 rounded text-sm ${key.is_active ? 'bg-red-600 hover:bg-red-700' : 'bg-green-600 hover:bg-green-700'} transition`;
      btnToggle.textContent = key.is_active ? 'Disable' : 'Enable';
      btnToggle.onclick = () => toggleKeyStatus(key.id, key.is_active);
      tdActions.appendChild(btnToggle);
      tr.appendChild(tdActions);
      
      tbody.appendChild(tr);
    });
    
  } catch (error) {
    console.error('Failed to load API keys:', error);
  }
}

async function toggleKeyStatus(keyId, isActive) {
  try {
    await adminApiCall(`/v1/admin/keys/${keyId}/toggle?active=${!isActive}`, {
      method: 'POST'
    });
    
    showSuccess(isActive ? 'Key disabled' : 'Key enabled');
    loadAllApiKeys();
    
  } catch (error) {
    showError(error.message);
  }
}

// Payments Tab
async function loadPayments() {
  try {
    const payments = await adminApiCall('/v1/admin/payments');
    
    const tbody = document.getElementById('paymentsTable');
    tbody.innerHTML = '';
    
    const pending = payments.filter(p => p.status === 'pending');
    
    if (pending.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5" class="text-center text-gray-500 py-8">No pending payments</td></tr>';
      return;
    }
    
    pending.forEach(payment => {
      const tr = document.createElement('tr');
      const userEmail = payment.ck_users ? payment.ck_users.email : 'Unknown';
      
      // Cell 1: Created date
      const tdDate = document.createElement('td');
      tdDate.textContent = new Date(payment.created_at).toLocaleString();
      tr.appendChild(tdDate);
      
      // Cell 2: User email (XSS risk!)
      const tdEmail = document.createElement('td');
      tdEmail.textContent = userEmail;
      tr.appendChild(tdEmail);
      
      // Cell 3: Plan badge
      const tdPlan = document.createElement('td');
      tdPlan.innerHTML = `<span class="plan-badge plan-${escapeHtml(payment.plan_requested)}">${escapeHtml(payment.plan_requested)}</span>`;
      tr.appendChild(tdPlan);
      
      // Cell 4: Amount
      const tdAmount = document.createElement('td');
      tdAmount.textContent = new Intl.NumberFormat('vi-VN').format(payment.amount_vnd) + ' VND';
      tr.appendChild(tdAmount);
      
      // Cell 5: Actions
      const tdActions = document.createElement('td');
      const btnConfirm = document.createElement('button');
      btnConfirm.className = 'bg-green-600 hover:bg-green-700 text-white px-3 py-1 rounded text-sm mr-2 transition';
      btnConfirm.textContent = 'Confirm';
      btnConfirm.onclick = () => confirmPaymentAdmin(payment.id);
      tdActions.appendChild(btnConfirm);
      
      const btnReject = document.createElement('button');
      btnReject.className = 'bg-red-600 hover:bg-red-700 text-white px-3 py-1 rounded text-sm transition';
      btnReject.textContent = 'Reject';
      btnReject.onclick = () => rejectPaymentAdmin(payment.id);
      tdActions.appendChild(btnReject);
      tr.appendChild(tdActions);
      
      tbody.appendChild(tr);
    });
    
  } catch (error) {
    console.error('Failed to load payments:', error);
  }
}

async function confirmPaymentAdmin(paymentId) {
  if (!confirm('Confirm this payment and upgrade the user?')) return;
  
  try {
    await adminApiCall(`/v1/admin/payments/${paymentId}/confirm`, {
      method: 'POST'
    });
    
    showSuccess('Payment confirmed');
    loadPayments();
    
  } catch (error) {
    showError(error.message);
  }
}

async function rejectPaymentAdmin(paymentId) {
  if (!confirm('Reject this payment?')) return;
  
  try {
    await adminApiCall(`/v1/admin/payments/${paymentId}/reject`, {
      method: 'POST'
    });
    
    showSuccess('Payment rejected');
    loadPayments();
    
  } catch (error) {
    showError(error.message);
  }
}

// Usage Tab
async function loadAdminUsage() {
  try {
    const stats = await adminApiCall('/v1/admin/stats');
    
    document.getElementById('totalUsers').textContent = stats.total_users || 0;
    document.getElementById('totalKeys').textContent = stats.total_keys || 0;
    document.getElementById('totalRequests').textContent = stats.total_requests || 0;
    document.getElementById('todayRequests').textContent = stats.today_requests || 0;
    
  } catch (error) {
    console.error('Failed to load admin usage:', error);
  }
}

// Settings Tab
async function loadSettings() {
  // Populate bank dropdown
  const bankSelect = document.getElementById('bankSelect');
  bankSelect.innerHTML = '';
  
  BANKS.forEach(bank => {
    const option = document.createElement('option');
    option.value = bank.code;
    option.textContent = `${bank.name} - ${bank.code}`;
    bankSelect.appendChild(option);
  });
  
  try {
    const settings = await adminApiCall('/v1/admin/settings');
    
    document.getElementById('bankSelect').value = settings.bank_id || '970422';
    document.getElementById('accountNumber').value = settings.bank_account || '';
    document.getElementById('accountHolder').value = settings.bank_holder || '';
    document.getElementById('starterPrice').value = settings.price_starter_vnd || 475000;
    document.getElementById('proPrice').value = settings.price_pro_vnd || 1975000;
    
    updateQRPreviews();
    
  } catch (error) {
    console.error('Failed to load settings:', error);
  }
  
  // Setup live QR preview update
  ['bankSelect', 'accountNumber', 'accountHolder', 'starterPrice', 'proPrice'].forEach(id => {
    document.getElementById(id).addEventListener('input', updateQRPreviews);
  });
}

function updateQRPreviews() {
  const bankId = document.getElementById('bankSelect').value;
  const accountNo = document.getElementById('accountNumber').value;
  const accountName = document.getElementById('accountHolder').value;
  const starterPrice = document.getElementById('starterPrice').value;
  const proPrice = document.getElementById('proPrice').value;
  
  if (bankId && accountNo && accountName) {
    const starterQR = `https://img.vietqr.io/image/${bankId}-${accountNo}-compact2.png?amount=${starterPrice}&addInfo=CRAWLKIT starter&accountName=${accountName}`;
    const proQR = `https://img.vietqr.io/image/${bankId}-${accountNo}-compact2.png?amount=${proPrice}&addInfo=CRAWLKIT pro&accountName=${accountName}`;
    
    document.getElementById('starterQR').src = starterQR;
    document.getElementById('proQR').src = proQR;
  }
}

async function saveSettings() {
  const settings = {
    bank_id: document.getElementById('bankSelect').value,
    bank_account: document.getElementById('accountNumber').value,
    bank_holder: document.getElementById('accountHolder').value,
    price_starter_vnd: document.getElementById('starterPrice').value,
    price_pro_vnd: document.getElementById('proPrice').value
  };
  
  try {
    await adminApiCall('/v1/admin/settings', {
      method: 'POST',
      body: JSON.stringify(settings)
    });
    
    showSuccess('Settings saved successfully');
    
  } catch (error) {
    showError(error.message);
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
