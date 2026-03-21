// Dashboard logic
let currentSection = 'overview';

// Check auth on load
if (!requireAuth()) {
  // Will redirect to login
}

const user = getUser();

// Initialize dashboard
document.addEventListener('DOMContentLoaded', async () => {
  // Set user info
  document.getElementById('userName').textContent = user.name;
  document.getElementById('welcomeName').textContent = user.name;
  
  // Set plan badge
  const planBadge = document.getElementById('planBadge');
  planBadge.textContent = user.plan || 'free';
  planBadge.className = `plan-badge plan-${user.plan || 'free'}`;
  
  // Load overview by default
  await loadOverview();
  
  // Setup sidebar navigation
  document.querySelectorAll('[data-section]').forEach(btn => {
    btn.addEventListener('click', (e) => {
      const section = e.target.getAttribute('data-section');
      switchSection(section);
    });
  });
  
  // Logout
  document.getElementById('logoutBtn').addEventListener('click', () => {
    clearAuth();
    window.location.href = '/login.html';
  });
});

function switchSection(section) {
  currentSection = section;
  
  // Update sidebar active state
  document.querySelectorAll('[data-section]').forEach(btn => {
    if (btn.getAttribute('data-section') === section) {
      btn.classList.add('sidebar-active');
    } else {
      btn.classList.remove('sidebar-active');
    }
  });
  
  // Hide all sections
  document.querySelectorAll('[data-content]').forEach(el => {
    el.classList.add('hidden');
  });
  
  // Show selected section
  document.getElementById(`${section}Section`).classList.remove('hidden');
  
  // Load section data
  switch(section) {
    case 'overview':
      loadOverview();
      break;
    case 'apikeys':
      loadApiKeys();
      break;
    case 'usage':
      loadUsage();
      break;
    case 'upgrade':
      loadUpgrade();
      break;
    case 'docs':
      loadDocs();
      break;
  }
}

// Overview
async function loadOverview() {
  try {
    const data = await apiCall('/v1/auth/usage');
    const stats = data.usage || data;
    
    document.getElementById('totalRequests').textContent = stats.total_requests || 0;
    document.getElementById('todayRequests').textContent = stats.total_requests || 0;
    document.getElementById('monthRequests').textContent = stats.total_requests || 0;
    const planLimits = { free: '20/hr', starter: '200/hr', pro: '1000/hr', enterprise: '∞' };
    document.getElementById('rateLimit').textContent = planLimits[user.plan] || '20/hr';
    
    // Set API key in code example
    const apiKey = getAuthToken();
    document.getElementById('exampleApiKey').textContent = maskKey(apiKey);
    
  } catch (error) {
    console.error('Failed to load overview:', error);
  }
}

function maskKey(key) {
  if (!key || key.length < 16) return '••••••••••••••••';
  return key.substring(0, 8) + '••••••••' + key.substring(key.length - 8);
}

function revealKey() {
  const apiKey = getAuthToken();
  const elem = document.getElementById('exampleApiKey');
  elem.textContent = apiKey;
  
  // Also reveal in SDK examples
  document.querySelectorAll('.masked-key').forEach(el => {
    el.textContent = apiKey;
  });
  
  showSuccess('API key revealed');
}

function copyKey() {
  const apiKey = getAuthToken();
  navigator.clipboard.writeText(apiKey);
  showSuccess('API key copied to clipboard');
}

function copyPythonExample() {
  const apiKey = getAuthToken();
  const code = `from crawlkit import CrawlKit

ck = CrawlKit("${apiKey}")
result = ck.scrape("https://example.com")
print(result.content)`;
  
  navigator.clipboard.writeText(code);
  showSuccess('Python example copied');
}

function copyNodeExample() {
  const apiKey = getAuthToken();
  const code = `const { CrawlKit } = require('paparusi-crawlkit');

const ck = new CrawlKit('${apiKey}');
const result = await ck.scrape('https://example.com');
console.log(result.content);`;
  
  navigator.clipboard.writeText(code);
  showSuccess('Node.js example copied');
}

function copyCurlExample() {
  const apiKey = getAuthToken();
  const code = `curl -X POST https://api.crawlkit.org/v1/crawl \\
  -H "X-API-Key: ${apiKey}" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com"}'`;
  
  navigator.clipboard.writeText(code);
  showSuccess('cURL example copied');
}

// Helper to escape HTML and prevent XSS
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}

// API Keys
async function loadApiKeys() {
  try {
    const data = await apiCall('/v1/auth/me');
    const keys = data.api_keys || [];
    
    const tbody = document.getElementById('apiKeysTable');
    tbody.innerHTML = '';
    
    if (!keys || keys.length === 0) {
      tbody.innerHTML = '<tr><td colspan="6" class="text-center text-gray-500 py-8">No API keys found</td></tr>';
      return;
    }
    
    keys.forEach(key => {
      const tr = document.createElement('tr');
      
      // Cell 1: Key name (user-controlled, must escape!)
      const tdName = document.createElement('td');
      tdName.textContent = key.name || 'Default';
      tr.appendChild(tdName);
      
      // Cell 2: Masked key
      const tdKey = document.createElement('td');
      tdKey.className = 'font-mono';
      tdKey.textContent = maskKey(key.key);
      tr.appendChild(tdKey);
      
      // Cell 3: Plan badge
      const tdPlan = document.createElement('td');
      tdPlan.innerHTML = `<span class="plan-badge plan-${escapeHtml(key.plan)}">${escapeHtml(key.plan)}</span>`;
      tr.appendChild(tdPlan);
      
      // Cell 4: Created date
      const tdDate = document.createElement('td');
      tdDate.textContent = new Date(key.created_at).toLocaleDateString();
      tr.appendChild(tdDate);
      
      // Cell 5: Status badge
      const tdStatus = document.createElement('td');
      const statusSpan = document.createElement('span');
      statusSpan.className = `px-2 py-1 rounded text-xs ${key.is_active ? 'bg-green-900 text-green-200' : 'bg-red-900 text-red-200'}`;
      statusSpan.textContent = key.is_active ? 'Active' : 'Revoked';
      tdStatus.appendChild(statusSpan);
      tr.appendChild(tdStatus);
      
      // Cell 6: Actions
      const tdActions = document.createElement('td');
      const btnCopy = document.createElement('button');
      btnCopy.className = 'text-indigo-500 hover:text-indigo-400 text-sm mr-3';
      btnCopy.textContent = 'Copy';
      btnCopy.onclick = () => copyApiKey(key.key);
      tdActions.appendChild(btnCopy);
      
      if (key.is_active) {
        const btnRevoke = document.createElement('button');
        btnRevoke.className = 'text-red-500 hover:text-red-400 text-sm';
        btnRevoke.textContent = 'Revoke';
        btnRevoke.onclick = () => revokeKey(key.id);
        tdActions.appendChild(btnRevoke);
      }
      tr.appendChild(tdActions);
      
      tbody.appendChild(tr);
    });
    
  } catch (error) {
    console.error('Failed to load API keys:', error);
  }
}

function copyApiKey(key) {
  navigator.clipboard.writeText(key);
  showSuccess('API key copied');
}

async function revokeKey(keyId) {
  if (!confirm('Are you sure you want to revoke this API key? This cannot be undone.')) {
    return;
  }
  
  try {
    await apiCall(`/v1/auth/keys/${keyId}`, { method: 'DELETE' });
    showSuccess('API key revoked');
    loadApiKeys();
  } catch (error) {
    showError(error.message);
  }
}

function openCreateKeyModal() {
  document.getElementById('createKeyModal').classList.remove('hidden');
}

function closeCreateKeyModal() {
  document.getElementById('createKeyModal').classList.add('hidden');
  document.getElementById('newKeyName').value = '';
}

async function createNewKey() {
  const name = document.getElementById('newKeyName').value.trim();
  
  if (!name) {
    showError('Please enter a key name');
    return;
  }
  
  try {
    const result = await apiCall('/v1/auth/keys', {
      method: 'POST',
      body: JSON.stringify({ name })
    });
    
    showSuccess('API key created');
    closeCreateKeyModal();
    loadApiKeys();
  } catch (error) {
    showError(error.message);
  }
}

// Usage
async function loadUsage() {
  try {
    const data = await apiCall('/v1/auth/usage');
    const usage = data.usage || data;
    
    // Render chart with placeholder data
    renderUsageChart([]);
    
    // Recent requests table
    const tbody = document.getElementById('recentRequestsTable');
    tbody.innerHTML = '';
    
    tbody.innerHTML = `<tr><td colspan="5" class="text-center text-gray-500 py-8">
      Total: ${usage.total_requests || 0} requests | 
      Success: ${usage.successful_requests || 0} | 
      Failed: ${usage.failed_requests || 0} |
      Chars: ${(usage.total_chars || 0).toLocaleString()}
    </td></tr>`;
    
  } catch (error) {
    console.error('Failed to load usage:', error);
  }
}

function renderUsageChart(data) {
  const ctx = document.getElementById('usageChart');
  
  // Simple bar chart with Chart.js
  if (window.Chart) {
    new Chart(ctx, {
      type: 'bar',
      data: {
        labels: data.map(d => d.date),
        datasets: [{
          label: 'Requests',
          data: data.map(d => d.count),
          backgroundColor: '#4f46e5'
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false }
        },
        scales: {
          y: { beginAtZero: true }
        }
      }
    });
  }
}

// Upgrade Plan
async function loadUpgrade() {
  const currentPlan = user.plan || 'free';
  
  // Highlight current plan
  document.querySelectorAll('[data-plan]').forEach(card => {
    if (card.getAttribute('data-plan') === currentPlan) {
      card.classList.add('border-indigo-600', 'border-2');
    } else {
      card.classList.remove('border-indigo-600', 'border-2');
    }
  });
}

async function upgradeToStarter() {
  await openPaymentModal('starter', 19);
}

async function upgradeToPro() {
  await openPaymentModal('pro', 79);
}

async function openPaymentModal(plan, amount) {
  document.getElementById('paymentModal').classList.remove('hidden');
  document.getElementById('paymentPlan').textContent = plan;
  document.getElementById('paymentAmount').textContent = `$${amount}`;
  
  try {
    // Fetch bank settings
    const settings = await apiCall('/v1/settings');
    
    const bankId = settings.bank_id || '970422';
    const accountNo = settings.bank_account || '0123456789';
    const accountName = encodeURIComponent(settings.bank_holder || 'CRAWLKIT');
    const email = user.email;
    const amountVnd = plan === 'starter' ? (settings.price_starter_vnd || 475000) : (settings.price_pro_vnd || 1975000);
    const memo = encodeURIComponent(`CRAWLKIT ${email} ${plan}`);
    
    document.getElementById('paymentAmount').textContent = new Intl.NumberFormat('vi-VN').format(amountVnd) + ' VND';
    
    const qrUrl = `https://img.vietqr.io/image/${bankId}-${accountNo}-compact2.png?amount=${amountVnd}&addInfo=${memo}&accountName=${accountName}`;
    
    document.getElementById('qrImage').src = qrUrl;
    document.getElementById('qrImage').classList.remove('hidden');
    
  } catch (error) {
    showError('Failed to load payment settings');
  }
}

function closePaymentModal() {
  document.getElementById('paymentModal').classList.add('hidden');
}

async function confirmPayment() {
  const plan = document.getElementById('paymentPlan').textContent;
  const amountText = document.getElementById('paymentAmount').textContent;
  const amountVnd = parseInt(amountText.replace(/[^\d]/g, ''));
  const memo = `CRAWLKIT ${user.email} ${plan}`;
  
  try {
    const result = await apiCall('/v1/payment/request', {
      method: 'POST',
      body: JSON.stringify({ 
        plan,
        amount_vnd: amountVnd,
        memo
      })
    });
    
    showSuccess('Payment request submitted. Please wait for confirmation.');
    closePaymentModal();
    
    // Show pending status if element exists
    const pendingElem = document.getElementById('pendingPayment');
    if (pendingElem) {
      pendingElem.classList.remove('hidden');
    }
    
  } catch (error) {
    showError(error.message);
  }
}

// Docs
function loadDocs() {
  // Static content, already in HTML
}
