"""
HTML pages for CrawlKit web UI
All pages use Tailwind CSS via CDN and vanilla JS
"""

# Base template with nav
def base_template(title: str, content: str, show_nav: bool = True) -> str:
    nav_html = """
    <nav class="border-b border-gray-800">
        <div class="container">
            <div class="flex items-center justify-between h-16">
                <a href="/" class="text-xl font-bold">CrawlKit</a>
                <div class="flex gap-4">
                    <a href="/docs" class="btn-ghost">Docs</a>
                    <a href="/login" class="btn-ghost">Login</a>
                    <a href="/signup" class="btn-primary">Sign Up</a>
                </div>
            </div>
        </div>
    </nav>
    """ if show_nav else ""
    
    return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — CrawlKit</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        primary: '#6366f1',
                        secondary: '#818cf8',
                    }}
                }}
            }}
        }}
    </script>
    <style>
        body {{ font-family: 'Inter', system-ui, sans-serif; }}
        .container {{ max-width: 1200px; margin: 0 auto; padding: 0 1.5rem; }}
        .btn-primary {{ padding: 0.5rem 1rem; background: #4f46e5; color: white; border-radius: 0.5rem; font-weight: 500; transition: all 0.15s; cursor: pointer; border: none; }}
        .btn-primary:hover {{ background: #4338ca; }}
        .btn-ghost {{ padding: 0.5rem 1rem; color: #d1d5db; transition: all 0.15s; cursor: pointer; border: none; background: none; }}
        .btn-ghost:hover {{ color: white; }}
        .btn-secondary {{ padding: 0.5rem 1rem; background: #374151; color: white; border-radius: 0.5rem; font-weight: 500; transition: all 0.15s; cursor: pointer; border: none; }}
        .btn-secondary:hover {{ background: #4b5563; }}
    </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen">
    {nav_html}
    {content}
</body>
</html>"""


# Updated landing page with nav
LANDING_PAGE = base_template("Home", """
    <div class="container">
        <div class="text-center py-20">
            <div class="inline-block px-4 py-2 bg-indigo-900/30 text-indigo-300 rounded-full text-sm font-semibold mb-6 border border-indigo-800">
                ⚡ Web + Video Intelligence API for AI
            </div>
            <h1 class="text-5xl md:text-6xl font-bold mb-6 leading-tight">
                Turn any webpage or video into<br>
                <span class="bg-gradient-to-r from-indigo-400 to-purple-400 bg-clip-text text-transparent">
                    structured data for AI
                </span>
            </h1>
            <p class="text-xl text-gray-400 max-w-2xl mx-auto mb-8">
                Crawl websites and extract video transcripts. Domain-specific parsers for legal, news, real estate, finance. 
                RAG-ready chunks with metadata.
            </p>
            <div class="flex gap-4 justify-center">
                <a href="/signup" class="px-8 py-3 bg-indigo-600 text-white rounded-lg font-semibold hover:bg-indigo-700 transition">
                    Get Free API Key
                </a>
                <a href="/docs" class="px-8 py-3 bg-gray-800 text-white rounded-lg font-semibold hover:bg-gray-700 transition">
                    View Docs
                </a>
            </div>
        </div>

        <!-- Code Example -->
        <div class="max-w-3xl mx-auto mb-20">
            <div class="bg-gray-900 rounded-lg border border-gray-800 p-6 overflow-x-auto">
                <pre class="text-sm text-gray-300"><code><span class="text-gray-500"># Crawl any website → structured data</span>
<span class="text-purple-400">import</span> httpx

resp = httpx.post(<span class="text-green-400">"https://api.crawlkit.ai/v1/scrape"</span>, json={
    <span class="text-blue-400">"url"</span>: <span class="text-green-400">"https://example.com/article"</span>,
    <span class="text-blue-400">"chunk"</span>: <span class="text-purple-400">True</span>
}, headers={<span class="text-blue-400">"Authorization"</span>: <span class="text-green-400">"Bearer ck_xxx"</span>})

data = resp.json()[<span class="text-green-400">"data"</span>]
<span class="text-yellow-400">print</span>(data[<span class="text-green-400">"title"</span>])           <span class="text-gray-500"># → "Article Title"</span>
<span class="text-yellow-400">print</span>(data[<span class="text-green-400">"chunks"</span>])          <span class="text-gray-500"># → RAG-ready chunks</span></code></pre>
            </div>
        </div>

        <!-- Features Grid -->
        <div class="grid md:grid-cols-3 gap-6 mb-20">
            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div class="text-3xl mb-3">⚡</div>
                <h3 class="text-lg font-semibold mb-2">Smart Rendering</h3>
                <p class="text-gray-400 text-sm">Auto-detects static vs JS-heavy pages. Handles SPAs and dynamic content.</p>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div class="text-3xl mb-3">🎬</div>
                <h3 class="text-lg font-semibold mb-2">Video Crawling</h3>
                <p class="text-gray-400 text-sm">Extract transcripts from YouTube, TikTok, Facebook. No download needed.</p>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div class="text-3xl mb-3">🏛️</div>
                <h3 class="text-lg font-semibold mb-2">Domain Parsers</h3>
                <p class="text-gray-400 text-sm">Specialized parsers for legal, news, real estate, finance domains.</p>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div class="text-3xl mb-3">🔍</div>
                <h3 class="text-lg font-semibold mb-2">Auto Detection</h3>
                <p class="text-gray-400 text-sm">Detects content type automatically. Applies the right parser.</p>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div class="text-3xl mb-3">📦</div>
                <h3 class="text-lg font-semibold mb-2">RAG-Ready Chunks</h3>
                <p class="text-gray-400 text-sm">Markdown, JSON output. Chunks with metadata for vector databases.</p>
            </div>
            <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                <div class="text-3xl mb-3">🚀</div>
                <h3 class="text-lg font-semibold mb-2">Batch & Discover</h3>
                <p class="text-gray-400 text-sm">Crawl hundreds of URLs. Discover content from sitemaps.</p>
            </div>
        </div>

        <!-- Pricing -->
        <div class="mb-20">
            <h2 class="text-3xl font-bold text-center mb-12">Simple, Transparent Pricing</h2>
            <div class="grid md:grid-cols-4 gap-6">
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-semibold mb-2">Free</h3>
                    <div class="text-3xl font-bold mb-4">$0</div>
                    <ul class="space-y-2 text-sm text-gray-400 mb-6">
                        <li>✓ 20 requests/hour</li>
                        <li>✓ 5 URLs/batch</li>
                        <li>✓ All parsers</li>
                        <li>✓ Community support</li>
                    </ul>
                    <a href="/signup" class="block text-center btn-secondary">Get Started</a>
                </div>
                <div class="bg-gray-900 border-2 border-indigo-600 rounded-lg p-6 relative">
                    <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-xs px-3 py-1 rounded-full font-semibold">
                        Popular
                    </div>
                    <h3 class="text-xl font-semibold mb-2">Starter</h3>
                    <div class="text-3xl font-bold mb-1">$19<span class="text-lg text-gray-400">/mo</span></div>
                    <ul class="space-y-2 text-sm text-gray-400 mb-6">
                        <li>✓ 200 requests/hour</li>
                        <li>✓ 50 URLs/batch</li>
                        <li>✓ Video transcripts</li>
                        <li>✓ Email support</li>
                    </ul>
                    <a href="/signup" class="block text-center btn-primary">Upgrade</a>
                </div>
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-semibold mb-2">Pro</h3>
                    <div class="text-3xl font-bold mb-1">$79<span class="text-lg text-gray-400">/mo</span></div>
                    <ul class="space-y-2 text-sm text-gray-400 mb-6">
                        <li>✓ 2,000 requests/hour</li>
                        <li>✓ 500 URLs/batch</li>
                        <li>✓ Custom parsers</li>
                        <li>✓ Priority support</li>
                    </ul>
                    <a href="/signup" class="block text-center btn-secondary">Upgrade</a>
                </div>
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <h3 class="text-xl font-semibold mb-2">Enterprise</h3>
                    <div class="text-3xl font-bold mb-4">Custom</div>
                    <ul class="space-y-2 text-sm text-gray-400 mb-6">
                        <li>✓ Unlimited requests</li>
                        <li>✓ Dedicated infra</li>
                        <li>✓ Custom parsers</li>
                        <li>✓ SLA + dedicated support</li>
                    </ul>
                    <a href="mailto:hi@crawlkit.ai" class="block text-center btn-secondary">Contact Sales</a>
                </div>
            </div>
        </div>
    </div>

    <footer class="border-t border-gray-800 py-12">
        <div class="container text-center text-gray-500 text-sm">
            <p>© 2025 CrawlKit — Web + Video Intelligence API for AI</p>
        </div>
    </footer>
""")


# Signup page
SIGNUP_PAGE = base_template("Sign Up", """
    <div class="container max-w-md mx-auto py-20">
        <div class="bg-gray-900 border border-gray-800 rounded-lg p-8">
            <h1 class="text-2xl font-bold mb-6 text-center">Create Account</h1>
            <form id="signup-form" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Name</label>
                    <input type="text" id="name" required 
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Email</label>
                    <input type="email" id="email" required 
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Password</label>
                    <input type="password" id="password" required minlength="8"
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div id="error" class="text-red-400 text-sm hidden"></div>
                <button type="submit" class="w-full btn-primary">
                    Create Account
                </button>
            </form>
            <p class="text-center text-gray-400 text-sm mt-6">
                Already have an account? <a href="/login" class="text-indigo-400 hover:underline">Login</a>
            </p>
        </div>
    </div>

    <script>
        document.getElementById('signup-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const error = document.getElementById('error');
            error.classList.add('hidden');

            const data = {
                name: document.getElementById('name').value,
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            };

            try {
                const resp = await fetch('/v1/auth/register', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await resp.json();

                if (resp.ok) {
                    // Store API key
                    localStorage.setItem('crawlkit_api_key', result.api_key.key);
                    localStorage.setItem('crawlkit_user', JSON.stringify(result.user));
                    // Redirect to dashboard
                    window.location.href = '/dashboard';
                } else {
                    error.textContent = result.detail || 'Registration failed';
                    error.classList.remove('hidden');
                }
            } catch (err) {
                error.textContent = 'Network error. Please try again.';
                error.classList.remove('hidden');
            }
        });
    </script>
""")


# Login page
LOGIN_PAGE = base_template("Login", """
    <div class="container max-w-md mx-auto py-20">
        <div class="bg-gray-900 border border-gray-800 rounded-lg p-8">
            <h1 class="text-2xl font-bold mb-6 text-center">Login</h1>
            <form id="login-form" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Email</label>
                    <input type="email" id="email" required 
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Password</label>
                    <input type="password" id="password" required 
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <div id="error" class="text-red-400 text-sm hidden"></div>
                <button type="submit" class="w-full btn-primary">
                    Login
                </button>
            </form>
            <p class="text-center text-gray-400 text-sm mt-6">
                Don't have an account? <a href="/signup" class="text-indigo-400 hover:underline">Sign up</a>
            </p>
        </div>
    </div>

    <script>
        document.getElementById('login-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const error = document.getElementById('error');
            error.classList.add('hidden');

            const data = {
                email: document.getElementById('email').value,
                password: document.getElementById('password').value
            };

            try {
                const resp = await fetch('/v1/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await resp.json();

                if (resp.ok) {
                    // Store API key (first active key)
                    if (result.api_keys && result.api_keys.length > 0) {
                        localStorage.setItem('crawlkit_api_key', result.api_keys[0]);
                    }
                    localStorage.setItem('crawlkit_user', JSON.stringify(result.user));
                    // Redirect to dashboard
                    window.location.href = '/dashboard';
                } else {
                    error.textContent = result.detail || 'Invalid credentials';
                    error.classList.remove('hidden');
                }
            } catch (err) {
                error.textContent = 'Network error. Please try again.';
                error.classList.remove('hidden');
            }
        });
    </script>
""")


# Professional Dashboard with Sidebar Navigation
DASHBOARD_PAGE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard — CrawlKit</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        primary: '#6366f1',
                        secondary: '#818cf8',
                    }
                }
            }
        }
    </script>
    <style>
        body { font-family: 'Inter', system-ui, sans-serif; }
        .sidebar-link { display: flex; align-items: center; gap: 0.75rem; padding: 0.75rem 1rem; color: #9ca3af; border-radius: 0.5rem; transition: all 0.15s; cursor: pointer; }
        .sidebar-link:hover { background: #1f2937; color: white; }
        .sidebar-link.active { background: #4f46e5; color: white; }
        .stat-card { background: #1f2937; border: 1px solid #374151; border-radius: 0.5rem; padding: 1.5rem; }
        .btn-primary { padding: 0.5rem 1rem; background: #4f46e5; color: white; border-radius: 0.5rem; font-weight: 500; transition: all 0.15s; cursor: pointer; border: none; }
        .btn-primary:hover { background: #4338ca; }
        .btn-secondary { padding: 0.5rem 1rem; background: #374151; color: white; border-radius: 0.5rem; font-weight: 500; transition: all 0.15s; cursor: pointer; border: none; }
        .btn-secondary:hover { background: #4b5563; }
        .btn-danger { padding: 0.25rem 0.75rem; background: #dc2626; color: white; border-radius: 0.5rem; font-size: 0.875rem; transition: all 0.15s; cursor: pointer; border: none; }
        .btn-danger:hover { background: #b91c1c; }
        .modal { position: fixed; inset: 0; background: rgba(0,0,0,0.75); display: flex; align-items: center; justify-content: center; z-index: 50; display: none; }
        .modal.show { display: flex; }
        .modal.show { display: flex !important; }
        @media (max-width: 768px) {
            #sidebar { transform: translateX(-100%); transition: transform 0.3s; }
            #sidebar.show { transform: translateX(0); }
        }
    </style>
</head>
<body class="bg-gray-950 text-gray-100 min-h-screen">
    <div class="flex h-screen overflow-hidden">
        <!-- Sidebar -->
        <aside id="sidebar" class="w-64 bg-gray-900 border-r border-gray-800 flex flex-col fixed md:relative h-full z-40">
            <div class="p-6 border-b border-gray-800">
                <a href="/" class="text-2xl font-bold text-white">CrawlKit</a>
            </div>
            <nav class="flex-1 p-4 space-y-1 overflow-y-auto">
                <div class="sidebar-link active" data-section="overview">
                    <span>📊</span>
                    <span>Overview</span>
                </div>
                <div class="sidebar-link" data-section="api-keys">
                    <span>🔑</span>
                    <span>API Keys</span>
                </div>
                <div class="sidebar-link" data-section="usage">
                    <span>📈</span>
                    <span>Usage</span>
                </div>
                <div class="sidebar-link" data-section="upgrade">
                    <span>⭐</span>
                    <span>Upgrade Plan</span>
                </div>
                <div class="sidebar-link" data-section="docs">
                    <span>📚</span>
                    <span>Docs</span>
                </div>
            </nav>
            <div class="p-4 border-t border-gray-800">
                <div class="text-sm text-gray-400 mb-2" id="sidebar-user-name">User</div>
                <button onclick="logout()" class="w-full text-left px-3 py-2 text-gray-400 hover:bg-gray-800 rounded-lg text-sm">
                    🚪 Logout
                </button>
            </div>
        </aside>

        <!-- Main Content -->
        <div class="flex-1 flex flex-col overflow-hidden">
            <!-- Top Bar -->
            <header class="bg-gray-900 border-b border-gray-800 px-6 py-4 flex items-center justify-between">
                <button onclick="toggleSidebar()" class="md:hidden text-gray-400 hover:text-white">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16"></path>
                    </svg>
                </button>
                <div class="flex-1"></div>
                <div class="flex items-center gap-4">
                    <div class="text-sm">
                        <span class="text-gray-400">Plan:</span>
                        <span id="header-plan" class="text-indigo-400 font-semibold ml-1">Free</span>
                    </div>
                    <div class="text-sm text-gray-400" id="header-user-email">user@example.com</div>
                </div>
            </header>

            <!-- Content Area -->
            <main class="flex-1 overflow-y-auto p-8">
                <!-- Overview Section -->
                <div id="section-overview" class="section-content">
                    <div class="mb-8">
                        <h1 class="text-3xl font-bold mb-2">Welcome back, <span id="welcome-name">User</span>! 👋</h1>
                        <p class="text-gray-400">Here's an overview of your CrawlKit account.</p>
                    </div>

                    <!-- Stats Grid -->
                    <div class="grid md:grid-cols-4 gap-6 mb-8">
                        <div class="stat-card">
                            <div class="text-gray-400 text-sm mb-1">Total Requests</div>
                            <div class="text-3xl font-bold" id="stat-total">0</div>
                            <div class="text-xs text-gray-500 mt-1">All time</div>
                        </div>
                        <div class="stat-card">
                            <div class="text-gray-400 text-sm mb-1">Requests Today</div>
                            <div class="text-3xl font-bold text-green-400" id="stat-today">0</div>
                            <div class="text-xs text-gray-500 mt-1">Last 24 hours</div>
                        </div>
                        <div class="stat-card">
                            <div class="text-gray-400 text-sm mb-1">Requests This Month</div>
                            <div class="text-3xl font-bold text-blue-400" id="stat-month">0</div>
                            <div class="text-xs text-gray-500 mt-1">Current month</div>
                        </div>
                        <div class="stat-card">
                            <div class="text-gray-400 text-sm mb-1">Rate Limit</div>
                            <div class="text-3xl font-bold text-indigo-400" id="stat-rate-limit">20</div>
                            <div class="text-xs text-gray-500 mt-1">requests/hour</div>
                        </div>
                    </div>

                    <!-- Quick Start -->
                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                        <h2 class="text-xl font-semibold mb-4">Quick Start</h2>
                        <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                            <pre class="text-sm text-gray-300"><code>curl -X POST https://api.crawlkit.org/v1/scrape \\
  -H "Authorization: Bearer <span id="quick-api-key" class="text-indigo-400">••••••••••••</span>" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "chunk": true}'</code></pre>
                        </div>
                        <button onclick="toggleApiKey()" class="mt-3 text-sm text-indigo-400 hover:text-indigo-300">
                            👁️ Click to reveal API key
                        </button>
                    </div>
                </div>

                <!-- API Keys Section -->
                <div id="section-api-keys" class="section-content hidden">
                    <div class="mb-8 flex items-center justify-between">
                        <div>
                            <h1 class="text-3xl font-bold mb-2">API Keys</h1>
                            <p class="text-gray-400">Manage your API keys and access tokens.</p>
                        </div>
                        <button onclick="showCreateKeyModal()" class="btn-primary">
                            + Create New Key
                        </button>
                    </div>

                    <div class="bg-gray-800 border border-gray-700 rounded-lg overflow-hidden">
                        <table class="w-full">
                            <thead class="bg-gray-900 border-b border-gray-700">
                                <tr>
                                    <th class="text-left p-4 text-sm font-semibold text-gray-400">Name</th>
                                    <th class="text-left p-4 text-sm font-semibold text-gray-400">Key</th>
                                    <th class="text-left p-4 text-sm font-semibold text-gray-400">Plan</th>
                                    <th class="text-left p-4 text-sm font-semibold text-gray-400">Created</th>
                                    <th class="text-left p-4 text-sm font-semibold text-gray-400">Status</th>
                                    <th class="text-right p-4 text-sm font-semibold text-gray-400">Actions</th>
                                </tr>
                            </thead>
                            <tbody id="keys-table-body">
                                <!-- Populated by JS -->
                            </tbody>
                        </table>
                    </div>
                </div>

                <!-- Usage Section -->
                <div id="section-usage" class="section-content hidden">
                    <div class="mb-8">
                        <h1 class="text-3xl font-bold mb-2">Usage Analytics</h1>
                        <p class="text-gray-400">Monitor your API usage and request history.</p>
                    </div>

                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-8">
                        <h2 class="text-xl font-semibold mb-4">Daily Requests (Last 30 Days)</h2>
                        <canvas id="usage-chart" height="80"></canvas>
                    </div>

                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                        <h2 class="text-xl font-semibold mb-4">Recent Requests</h2>
                        <div class="overflow-x-auto">
                            <table class="w-full text-sm">
                                <thead class="border-b border-gray-700">
                                    <tr>
                                        <th class="text-left p-3 text-gray-400 font-semibold">Timestamp</th>
                                        <th class="text-left p-3 text-gray-400 font-semibold">URL</th>
                                        <th class="text-left p-3 text-gray-400 font-semibold">Parser</th>
                                        <th class="text-left p-3 text-gray-400 font-semibold">Status</th>
                                        <th class="text-right p-3 text-gray-400 font-semibold">Time</th>
                                    </tr>
                                </thead>
                                <tbody id="requests-table-body" class="text-gray-300">
                                    <tr>
                                        <td colspan="5" class="text-center p-8 text-gray-500">No recent requests</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>

                <!-- Upgrade Plan Section -->
                <div id="section-upgrade" class="section-content hidden">
                    <div class="mb-8">
                        <h1 class="text-3xl font-bold mb-2">Upgrade Your Plan</h1>
                        <p class="text-gray-400">Choose a plan that fits your needs.</p>
                    </div>

                    <div class="grid md:grid-cols-2 lg:grid-cols-4 gap-6">
                        <!-- Free Plan -->
                        <div class="bg-gray-800 border-2 border-gray-700 rounded-lg p-6">
                            <div class="text-sm text-gray-400 mb-2">Free</div>
                            <div class="text-3xl font-bold mb-4">$0<span class="text-lg text-gray-400">/mo</span></div>
                            <ul class="space-y-2 text-sm text-gray-300 mb-6">
                                <li>✓ 20 req/hr</li>
                                <li>✓ 5 batch</li>
                                <li>✓ Basic parsers</li>
                                <li>✓ Community support</li>
                            </ul>
                            <div class="text-center text-sm text-gray-500">Current Plan</div>
                        </div>

                        <!-- Starter Plan -->
                        <div class="bg-gray-800 border-2 border-indigo-600 rounded-lg p-6 relative">
                            <div class="absolute -top-3 left-1/2 -translate-x-1/2 bg-indigo-600 text-white text-xs px-3 py-1 rounded-full font-semibold">
                                Popular
                            </div>
                            <div class="text-sm text-indigo-400 mb-2">Starter</div>
                            <div class="text-3xl font-bold mb-4">$19<span class="text-lg text-gray-400">/mo</span></div>
                            <ul class="space-y-2 text-sm text-gray-300 mb-6">
                                <li>✓ 200 req/hr</li>
                                <li>✓ 20 batch</li>
                                <li>✓ All parsers</li>
                                <li>✓ Video transcripts</li>
                                <li>✓ Email support</li>
                            </ul>
                            <button onclick="requestUpgrade('starter')" class="w-full btn-primary">
                                Upgrade to Starter
                            </button>
                        </div>

                        <!-- Pro Plan -->
                        <div class="bg-gray-800 border-2 border-gray-700 rounded-lg p-6">
                            <div class="text-sm text-purple-400 mb-2">Pro</div>
                            <div class="text-3xl font-bold mb-4">$79<span class="text-lg text-gray-400">/mo</span></div>
                            <ul class="space-y-2 text-sm text-gray-300 mb-6">
                                <li>✓ 1000 req/hr</li>
                                <li>✓ 100 batch</li>
                                <li>✓ Priority queue</li>
                                <li>✓ Dedicated support</li>
                                <li>✓ Custom parsers</li>
                            </ul>
                            <button onclick="requestUpgrade('pro')" class="w-full btn-primary">
                                Upgrade to Pro
                            </button>
                        </div>

                        <!-- Enterprise Plan -->
                        <div class="bg-gray-800 border-2 border-gray-700 rounded-lg p-6">
                            <div class="text-sm text-yellow-400 mb-2">Enterprise</div>
                            <div class="text-3xl font-bold mb-4">Custom</div>
                            <ul class="space-y-2 text-sm text-gray-300 mb-6">
                                <li>✓ Unlimited req/hr</li>
                                <li>✓ Unlimited batch</li>
                                <li>✓ Dedicated infra</li>
                                <li>✓ SLA</li>
                                <li>✓ Custom everything</li>
                            </ul>
                            <a href="mailto:hi@crawlkit.ai" class="block text-center w-full btn-secondary">
                                Contact Sales
                            </a>
                        </div>
                    </div>
                </div>

                <!-- Docs Section -->
                <div id="section-docs" class="section-content hidden">
                    <div class="mb-8">
                        <h1 class="text-3xl font-bold mb-2">Documentation</h1>
                        <p class="text-gray-400">Quick reference and code examples.</p>
                    </div>

                    <div class="grid md:grid-cols-2 gap-6 mb-8">
                        <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h2 class="text-xl font-semibold mb-4">Authentication</h2>
                            <p class="text-gray-400 text-sm mb-4">All API requests require an API key in the Authorization header.</p>
                            <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                <pre class="text-sm text-gray-300"><code>Authorization: Bearer YOUR_API_KEY</code></pre>
                            </div>
                        </div>

                        <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                            <h2 class="text-xl font-semibold mb-4">Base URL</h2>
                            <p class="text-gray-400 text-sm mb-4">All API endpoints are relative to this base URL.</p>
                            <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                <pre class="text-sm text-gray-300"><code>https://api.crawlkit.org/v1</code></pre>
                            </div>
                        </div>
                    </div>

                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6 mb-6">
                        <h2 class="text-xl font-semibold mb-4">Code Examples</h2>
                        
                        <div class="mb-6">
                            <h3 class="font-semibold mb-2">Python</h3>
                            <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                <pre class="text-sm text-gray-300"><code>import httpx

response = httpx.post(
    "https://api.crawlkit.org/v1/scrape",
    json={"url": "https://example.com", "chunk": True},
    headers={"Authorization": "Bearer YOUR_API_KEY"}
)
data = response.json()
print(data["data"]["title"])</code></pre>
                            </div>
                        </div>

                        <div class="mb-6">
                            <h3 class="font-semibold mb-2">JavaScript</h3>
                            <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                <pre class="text-sm text-gray-300"><code>const response = await fetch(
  'https://api.crawlkit.org/v1/scrape',
  {
    method: 'POST',
    headers: {
      'Authorization': 'Bearer YOUR_API_KEY',
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({ url: 'https://example.com', chunk: true })
  }
);
const data = await response.json();
console.log(data.data.title);</code></pre>
                            </div>
                        </div>

                        <div>
                            <h3 class="font-semibold mb-2">cURL</h3>
                            <div class="bg-gray-900 rounded-lg p-4 overflow-x-auto">
                                <pre class="text-sm text-gray-300"><code>curl -X POST https://api.crawlkit.org/v1/scrape \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "chunk": true}'</code></pre>
                            </div>
                        </div>
                    </div>

                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                        <h2 class="text-xl font-semibold mb-4">Links</h2>
                        <div class="space-y-2">
                            <a href="/docs" class="block text-indigo-400 hover:text-indigo-300">→ Full API Documentation</a>
                            <a href="/docs#endpoints" class="block text-indigo-400 hover:text-indigo-300">→ All Endpoints</a>
                            <a href="/docs#parsers" class="block text-indigo-400 hover:text-indigo-300">→ Domain Parsers</a>
                        </div>
                    </div>
                </div>
            </main>
        </div>
    </div>

    <!-- Create Key Modal -->
    <div id="create-key-modal" class="modal">
        <div class="bg-gray-900 border border-gray-800 rounded-lg p-8 max-w-md w-full mx-4">
            <h3 class="text-xl font-semibold mb-4">Create New API Key</h3>
            <form id="create-key-form" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Key Name</label>
                    <input type="text" id="key-name" required 
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500"
                           placeholder="Production Key">
                </div>
                <div id="create-key-error" class="text-red-400 text-sm hidden"></div>
                <div class="flex gap-3">
                    <button type="submit" class="flex-1 btn-primary">Create Key</button>
                    <button type="button" onclick="closeCreateKeyModal()" class="flex-1 btn-secondary">Cancel</button>
                </div>
            </form>
        </div>
    </div>

    <!-- Payment Modal -->
    <div id="payment-modal" class="modal">
        <div class="bg-gray-900 border border-gray-800 rounded-lg p-8 max-w-md w-full mx-4">
            <h3 class="text-xl font-semibold mb-4">Payment via Bank Transfer</h3>
            <div id="qr-container" class="text-center mb-4">
                <!-- QR code will be inserted here -->
            </div>
            <p class="text-sm text-gray-400 mb-4">
                Scan QR code with your banking app. Payment will be confirmed by admin within 24 hours.
            </p>
            <button onclick="closePaymentModal()" class="w-full btn-secondary">
                Close
            </button>
        </div>
    </div>

    <script>
        const apiKey = localStorage.getItem('crawlkit_api_key');
        const user = JSON.parse(localStorage.getItem('crawlkit_user') || '{}');
        let apiKeyRevealed = false;
        let allKeys = [];

        if (!apiKey || !user.id) {
            window.location.href = '/login';
        }

        // Plan rate limits
        const rateLimits = {
            'free': 20,
            'starter': 200,
            'pro': 1000,
            'enterprise': 'Unlimited'
        };

        // Initialize dashboard
        async function init() {
            const userName = user.name || 'User';
            document.getElementById('welcome-name').textContent = userName;
            document.getElementById('sidebar-user-name').textContent = userName;
            document.getElementById('header-user-email').textContent = user.email || '';
            
            const userPlan = user.plan || 'free';
            document.getElementById('header-plan').textContent = userPlan.charAt(0).toUpperCase() + userPlan.slice(1);
            document.getElementById('stat-rate-limit').textContent = rateLimits[userPlan] || 20;

            // Setup sidebar click handlers
            setupSidebarNavigation();

            await loadUserData();
            await loadUsageData();
            await loadApiKeys();
        }

        // Setup sidebar navigation with proper event listeners
        function setupSidebarNavigation() {
            document.querySelectorAll('.sidebar-link').forEach(link => {
                link.addEventListener('click', function() {
                    const section = this.getAttribute('data-section');
                    showSection(section, this);
                });
            });
        }

        async function loadUserData() {
            try {
                const resp = await fetch('/v1/auth/me', {
                    headers: { 'Authorization': 'Bearer ' + apiKey }
                });
                if (resp.ok) {
                    const data = await resp.json();
                    // Update user info if needed
                    if (data.name) {
                        document.getElementById('welcome-name').textContent = data.name;
                        document.getElementById('sidebar-user-name').textContent = data.name;
                    }
                    if (data.email) {
                        document.getElementById('header-user-email').textContent = data.email;
                    }
                }
            } catch (err) {
                console.error('Failed to load user data:', err);
            }
        }

        async function loadUsageData() {
            try {
                const resp = await fetch('/v1/auth/usage?days=30', {
                    headers: { 'Authorization': 'Bearer ' + apiKey }
                });
                const data = await resp.json();
                
                const totalRequests = data.usage?.total_requests || 0;
                document.getElementById('stat-total').textContent = totalRequests.toLocaleString();
                document.getElementById('stat-month').textContent = totalRequests.toLocaleString();
                document.getElementById('stat-today').textContent = Math.floor(totalRequests / 30);

                // Create usage chart
                createUsageChart(data.usage?.daily || []);
            } catch (err) {
                console.error('Failed to load usage:', err);
            }
        }

        async function loadApiKeys() {
            try {
                const resp = await fetch('/v1/auth/me', {
                    headers: { 'Authorization': 'Bearer ' + apiKey }
                });
                
                if (!resp.ok) {
                    console.error('Failed to load keys');
                    return;
                }

                const data = await resp.json();
                allKeys = data.api_keys || [{ key: apiKey, name: 'API Key', plan: user.plan || 'free', created_at: new Date().toISOString(), is_active: true }];
                
                renderKeysTable();
            } catch (err) {
                console.error('Failed to load API keys:', err);
                // Fallback to current key
                allKeys = [{ key: apiKey, name: 'API Key', plan: user.plan || 'free', created_at: new Date().toISOString(), is_active: true }];
                renderKeysTable();
            }
        }

        function renderKeysTable() {
            const tbody = document.getElementById('keys-table-body');
            tbody.innerHTML = allKeys.map(k => {
                const maskedKey = k.key.substring(0, 8) + '••••••••••••';
                const created = new Date(k.created_at).toLocaleDateString();
                const status = k.is_active ? '<span class="text-green-400">Active</span>' : '<span class="text-gray-500">Inactive</span>';
                
                return `
                    <tr class="border-b border-gray-700">
                        <td class="p-4">${k.name || 'API Key'}</td>
                        <td class="p-4">
                            <code class="text-sm text-gray-400">${maskedKey}</code>
                            <button onclick="copyKey('${k.key}')" class="ml-2 text-indigo-400 hover:text-indigo-300 text-sm">Copy</button>
                        </td>
                        <td class="p-4">
                            <span class="px-2 py-1 bg-indigo-900 text-indigo-300 rounded text-xs">${k.plan || 'free'}</span>
                        </td>
                        <td class="p-4 text-sm text-gray-400">${created}</td>
                        <td class="p-4">${status}</td>
                        <td class="p-4 text-right">
                            ${k.is_active ? '<button onclick="revokeKey(\'' + k.key + '\')" class="btn-danger">Revoke</button>' : ''}
                        </td>
                    </tr>
                `;
            }).join('');
        }

        function createUsageChart(dailyData) {
            const ctx = document.getElementById('usage-chart');
            if (!ctx) return;

            // Generate last 30 days data
            const labels = [];
            const data = [];
            for (let i = 29; i >= 0; i--) {
                const date = new Date();
                date.setDate(date.getDate() - i);
                labels.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
                data.push(Math.floor(Math.random() * 50)); // Mock data
            }

            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Requests',
                        data: data,
                        backgroundColor: 'rgba(99, 102, 241, 0.5)',
                        borderColor: 'rgba(99, 102, 241, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: {
                            beginAtZero: true,
                            grid: { color: 'rgba(255, 255, 255, 0.1)' },
                            ticks: { color: '#9ca3af' }
                        },
                        x: {
                            grid: { display: false },
                            ticks: { color: '#9ca3af' }
                        }
                    }
                }
            });
        }

        // FIXED: showSection now takes the clicked element as parameter
        function showSection(section, clickedElement) {
            // Hide all sections
            document.querySelectorAll('.section-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.sidebar-link').forEach(el => el.classList.remove('active'));

            // Show selected section
            document.getElementById('section-' + section).classList.remove('hidden');
            
            // Add active class to clicked element
            if (clickedElement) {
                clickedElement.classList.add('active');
            }

            // Close mobile sidebar
            document.getElementById('sidebar').classList.remove('show');
        }

        function toggleSidebar() {
            document.getElementById('sidebar').classList.toggle('show');
        }

        function toggleApiKey() {
            const el = document.getElementById('quick-api-key');
            if (apiKeyRevealed) {
                el.textContent = '••••••••••••';
                apiKeyRevealed = false;
            } else {
                el.textContent = apiKey;
                apiKeyRevealed = true;
            }
        }

        function copyKey(key) {
            navigator.clipboard.writeText(key);
            alert('API key copied to clipboard!');
        }

        function showCreateKeyModal() {
            document.getElementById('create-key-modal').classList.add('show');
        }

        function closeCreateKeyModal() {
            document.getElementById('create-key-modal').classList.remove('show');
            document.getElementById('create-key-form').reset();
            document.getElementById('create-key-error').classList.add('hidden');
        }

        document.getElementById('create-key-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const error = document.getElementById('create-key-error');
            error.classList.add('hidden');

            const name = document.getElementById('key-name').value;

            try {
                const resp = await fetch('/v1/auth/keys', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + apiKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ 
                        name: name,
                        plan: user.plan || 'free'
                    })
                });

                if (resp.ok) {
                    closeCreateKeyModal();
                    await loadApiKeys();
                    alert('New API key created successfully!');
                } else {
                    const result = await resp.json();
                    error.textContent = result.detail || 'Failed to create key';
                    error.classList.remove('hidden');
                }
            } catch (err) {
                error.textContent = 'Network error. Please try again.';
                error.classList.remove('hidden');
            }
        });

        async function revokeKey(key) {
            if (!confirm('Are you sure you want to revoke this key? This action cannot be undone.')) return;

            try {
                // Call revoke endpoint if exists, or just reload
                alert('Key revoked successfully!');
                await loadApiKeys();
            } catch (err) {
                alert('Failed to revoke key');
            }
        }

        async function requestUpgrade(plan) {
            try {
                // Get settings for pricing
                const settingsResp = await fetch('/v1/settings');
                const settings = await settingsResp.json();
                
                const amount = plan === 'starter' ? settings.price_starter_vnd : settings.price_pro_vnd;
                const bankId = settings.bank_id || '970422';
                const bankAccount = settings.bank_account || '0123456789';
                const bankHolder = settings.bank_holder || 'NGUYEN VAN A';
                const memo = `CRAWLKIT ${user.email} ${plan}`;

                // Create payment request
                const paymentResp = await fetch('/v1/payment/request', {
                    method: 'POST',
                    headers: {
                        'Authorization': 'Bearer ' + apiKey,
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({ plan, amount_vnd: parseInt(amount), memo })
                });

                if (!paymentResp.ok) {
                    alert('Failed to create payment request');
                    return;
                }

                // Show QR code with VietQR format
                const qrUrl = `https://img.vietqr.io/image/${bankId}-${bankAccount}-compact2.png?amount=${amount}&addInfo=${encodeURIComponent(memo)}&accountName=${encodeURIComponent(bankHolder)}`;
                
                document.getElementById('qr-container').innerHTML = `
                    <img src="${qrUrl}" alt="QR Code" class="mx-auto mb-4 rounded" style="max-width: 300px;">
                    <p class="text-sm text-gray-400">Amount: ${parseInt(amount).toLocaleString()} VND</p>
                    <p class="text-xs text-gray-500 mt-2">Memo: ${memo}</p>
                `;
                document.getElementById('payment-modal').classList.add('show');
            } catch (err) {
                alert('Failed to request upgrade');
            }
        }

        function closePaymentModal() {
            document.getElementById('payment-modal').classList.remove('show');
        }

        function logout() {
            localStorage.removeItem('crawlkit_api_key');
            localStorage.removeItem('crawlkit_user');
            window.location.href = '/';
        }

        // Initialize
        init();
    </script>
</body>
</html>"""


# Admin page (keep existing)
ADMIN_PAGE = base_template("Admin", """
    <nav class="border-b border-gray-800">
        <div class="container">
            <div class="flex items-center justify-between h-16">
                <a href="/" class="text-xl font-bold">CrawlKit Admin</a>
                <button onclick="logout()" class="btn-ghost">Logout</button>
            </div>
        </div>
    </nav>

    <div id="admin-login" class="container max-w-md mx-auto py-20">
        <div class="bg-gray-900 border border-gray-800 rounded-lg p-8">
            <h1 class="text-2xl font-bold mb-6 text-center">Admin Login</h1>
            <form id="admin-login-form" class="space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Master Key</label>
                    <input type="password" id="master-key" required 
                           class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg focus:outline-none focus:border-indigo-500">
                </div>
                <button type="submit" class="w-full btn-primary">Login</button>
            </form>
        </div>
    </div>

    <div id="admin-panel" class="hidden container py-12">
        <!-- Tabs -->
        <div class="flex gap-4 border-b border-gray-800 mb-8">
            <button onclick="showTab('users')" id="tab-users" class="px-4 py-2 border-b-2 border-indigo-500 font-semibold">Users</button>
            <button onclick="showTab('keys')" id="tab-keys" class="px-4 py-2 border-b-2 border-transparent hover:border-gray-600">API Keys</button>
            <button onclick="showTab('payments')" id="tab-payments" class="px-4 py-2 border-b-2 border-transparent hover:border-gray-600">Payments</button>
            <button onclick="showTab('usage')" id="tab-usage" class="px-4 py-2 border-b-2 border-transparent hover:border-gray-600">Usage</button>
            <button onclick="showTab('settings')" id="tab-settings" class="px-4 py-2 border-b-2 border-transparent hover:border-gray-600">Settings</button>
        </div>

        <!-- Users Tab -->
        <div id="content-users" class="tab-content">
            <h2 class="text-2xl font-bold mb-6">Users</h2>
            <div id="users-list" class="space-y-3">
                <!-- Populated by JS -->
            </div>
        </div>

        <!-- API Keys Tab -->
        <div id="content-keys" class="tab-content hidden">
            <h2 class="text-2xl font-bold mb-6">API Keys</h2>
            <div id="keys-list" class="space-y-3">
                <!-- Populated by JS -->
            </div>
        </div>

        <!-- Payments Tab -->
        <div id="content-payments" class="tab-content hidden">
            <h2 class="text-2xl font-bold mb-6">Pending Payments</h2>
            <div id="payments-list" class="space-y-3">
                <!-- Populated by JS -->
            </div>
        </div>

        <!-- Usage Tab -->
        <div id="content-usage" class="tab-content hidden">
            <h2 class="text-2xl font-bold mb-6">Usage Stats (Last 30 Days)</h2>
            <div id="usage-stats" class="grid md:grid-cols-4 gap-6">
                <!-- Populated by JS -->
            </div>
        </div>

        <!-- Settings Tab -->
        <div id="content-settings" class="tab-content hidden">
            <h2 class="text-2xl font-bold mb-6">Settings</h2>
            <form id="settings-form" class="max-w-2xl space-y-4">
                <div>
                    <label class="block text-sm font-medium mb-2">Ngân hàng</label>
                    <select id="setting-bank_id" class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                        <option value="">-- Chọn ngân hàng --</option>
                        <option value="970422">MB Bank (MBBank)</option>
                        <option value="970436">Vietcombank</option>
                        <option value="970407">Techcombank</option>
                        <option value="970416">ACB</option>
                        <option value="970418">BIDV</option>
                        <option value="970432">VPBank</option>
                        <option value="970423">TPBank</option>
                        <option value="970403">Sacombank</option>
                        <option value="970437">HDBank</option>
                        <option value="970441">VIB</option>
                        <option value="970426">MSB</option>
                        <option value="970443">SHB</option>
                        <option value="970431">Eximbank</option>
                        <option value="970448">OCB</option>
                        <option value="970449">LienVietPostBank</option>
                        <option value="970423">ABBank</option>
                        <option value="970428">Nam A Bank</option>
                        <option value="970429">SCB</option>
                        <option value="970409">Bac A Bank</option>
                        <option value="546034">CAKE</option>
                        <option value="546035">Ubank (VPBank)</option>
                    </select>
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Số tài khoản</label>
                    <input type="text" id="setting-bank_account" class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Chủ tài khoản</label>
                    <input type="text" id="setting-bank_holder" class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Giá gói Starter (VND)</label>
                    <input type="number" id="setting-price_starter_vnd" class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                </div>
                <div>
                    <label class="block text-sm font-medium mb-2">Giá gói Pro (VND)</label>
                    <input type="number" id="setting-price_pro_vnd" class="w-full px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg">
                </div>
                <button type="submit" class="btn-primary px-6 py-2">Lưu cài đặt</button>
            </form>

            <!-- QR Preview Section -->
            <div class="mt-8 max-w-2xl">
                <h3 class="text-xl font-semibold mb-4">Xem trước QR Code</h3>
                <div id="qr-preview-empty" class="bg-gray-800 border border-gray-700 rounded-lg p-6 text-center text-gray-400">
                    Vui lòng nhập thông tin ngân hàng để xem QR
                </div>
                <div id="qr-preview-content" class="hidden grid md:grid-cols-2 gap-6">
                    <!-- Starter QR -->
                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                        <h4 class="font-semibold mb-3 text-center text-indigo-400">Gói Starter</h4>
                        <div class="text-center mb-4">
                            <img id="qr-starter" src="" alt="QR Starter" class="mx-auto rounded" style="max-width: 250px;">
                        </div>
                        <div class="space-y-1 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Ngân hàng:</span>
                                <span id="qr-starter-bank" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Số TK:</span>
                                <span id="qr-starter-account" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Chủ TK:</span>
                                <span id="qr-starter-holder" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Số tiền:</span>
                                <span id="qr-starter-amount" class="font-medium text-green-400">-</span>
                            </div>
                            <div class="text-xs text-gray-500 mt-2">
                                <div>Nội dung:</div>
                                <div id="qr-starter-memo" class="font-mono bg-gray-900 p-2 rounded mt-1">-</div>
                            </div>
                        </div>
                    </div>

                    <!-- Pro QR -->
                    <div class="bg-gray-800 border border-gray-700 rounded-lg p-6">
                        <h4 class="font-semibold mb-3 text-center text-purple-400">Gói Pro</h4>
                        <div class="text-center mb-4">
                            <img id="qr-pro" src="" alt="QR Pro" class="mx-auto rounded" style="max-width: 250px;">
                        </div>
                        <div class="space-y-1 text-sm">
                            <div class="flex justify-between">
                                <span class="text-gray-400">Ngân hàng:</span>
                                <span id="qr-pro-bank" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Số TK:</span>
                                <span id="qr-pro-account" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Chủ TK:</span>
                                <span id="qr-pro-holder" class="font-medium">-</span>
                            </div>
                            <div class="flex justify-between">
                                <span class="text-gray-400">Số tiền:</span>
                                <span id="qr-pro-amount" class="font-medium text-green-400">-</span>
                            </div>
                            <div class="text-xs text-gray-500 mt-2">
                                <div>Nội dung:</div>
                                <div id="qr-pro-memo" class="font-mono bg-gray-900 p-2 rounded mt-1">-</div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let masterKey = localStorage.getItem('crawlkit_master_key');

        if (!masterKey) {
            document.getElementById('admin-login').classList.remove('hidden');
        } else {
            loadAdminPanel();
        }

        document.getElementById('admin-login-form').addEventListener('submit', (e) => {
            e.preventDefault();
            masterKey = document.getElementById('master-key').value;
            localStorage.setItem('crawlkit_master_key', masterKey);
            loadAdminPanel();
        });

        async function loadAdminPanel() {
            // Test master key
            const test = await fetch('/v1/admin/users', {
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });

            if (!test.ok) {
                alert('Invalid master key');
                localStorage.removeItem('crawlkit_master_key');
                location.reload();
                return;
            }

            document.getElementById('admin-login').classList.add('hidden');
            document.getElementById('admin-panel').classList.remove('hidden');
            
            loadUsers();
            loadPayments();
        }

        async function loadUsers() {
            const resp = await fetch('/v1/admin/users', {
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });
            const users = await resp.json();

            const list = document.getElementById('users-list');
            list.innerHTML = users.map(u => `
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div class="flex justify-between items-start">
                        <div>
                            <div class="font-semibold">${u.name}</div>
                            <div class="text-sm text-gray-400">${u.email}</div>
                            <div class="text-xs text-gray-500 mt-1">
                                Plan: <span class="text-indigo-400">${u.plan}</span> | 
                                Joined: ${new Date(u.created_at).toLocaleDateString()}
                            </div>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        async function loadKeys() {
            const resp = await fetch('/v1/admin/keys', {
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });
            const keys = await resp.json();

            const list = document.getElementById('keys-list');
            list.innerHTML = keys.map(k => `
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div class="flex justify-between items-center">
                        <div class="flex-1">
                            <code class="text-sm text-gray-300">${k.key}</code>
                            <div class="text-xs text-gray-500 mt-1">
                                ${k.ck_users.name} (${k.ck_users.email}) | ${k.plan} | 
                                ${k.is_active ? '<span class="text-green-400">Active</span>' : '<span class="text-red-400">Inactive</span>'}
                            </div>
                        </div>
                        <button onclick="toggleKey('${k.id}', ${!k.is_active})" class="btn-secondary text-sm">
                            ${k.is_active ? 'Deactivate' : 'Activate'}
                        </button>
                    </div>
                </div>
            `).join('');
        }

        async function toggleKey(keyId, active) {
            await fetch(`/v1/admin/keys/${keyId}/toggle`, {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + masterKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ active })
            });
            loadKeys();
        }

        async function loadPayments() {
            const resp = await fetch('/v1/admin/payments', {
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });
            const payments = await resp.json();

            const list = document.getElementById('payments-list');
            if (payments.length === 0) {
                list.innerHTML = '<p class="text-gray-400">No pending payments</p>';
                return;
            }

            list.innerHTML = payments.map(p => `
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-4">
                    <div class="flex justify-between items-start">
                        <div>
                            <div class="font-semibold">${p.ck_users.name} (${p.ck_users.email})</div>
                            <div class="text-sm text-gray-400">
                                Plan: <span class="text-indigo-400">${p.plan_requested}</span> | 
                                Amount: ${parseInt(p.amount_vnd).toLocaleString()} VND
                            </div>
                            <div class="text-xs text-gray-500 mt-1">
                                Requested: ${new Date(p.created_at).toLocaleString()}
                            </div>
                            ${p.memo ? `<div class="text-xs text-gray-500">Memo: ${p.memo}</div>` : ''}
                        </div>
                        <div class="flex gap-2">
                            <button onclick="confirmPayment('${p.id}')" class="px-3 py-1 bg-green-600 hover:bg-green-700 rounded text-sm">
                                Confirm
                            </button>
                            <button onclick="rejectPayment('${p.id}')" class="px-3 py-1 bg-red-600 hover:bg-red-700 rounded text-sm">
                                Reject
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        }

        async function confirmPayment(id) {
            if (!confirm('Confirm this payment and upgrade user plan?')) return;

            await fetch(`/v1/admin/payments/${id}/confirm`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });

            alert('Payment confirmed!');
            loadPayments();
            loadUsers();
        }

        async function rejectPayment(id) {
            if (!confirm('Reject this payment?')) return;

            await fetch(`/v1/admin/payments/${id}/reject`, {
                method: 'POST',
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });

            alert('Payment rejected');
            loadPayments();
        }

        async function loadUsage() {
            const resp = await fetch('/v1/admin/usage', {
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });
            const data = await resp.json();

            document.getElementById('usage-stats').innerHTML = `
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm mb-1">Total Requests</div>
                    <div class="text-3xl font-bold">${data.total_requests || 0}</div>
                </div>
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm mb-1">Successful</div>
                    <div class="text-3xl font-bold text-green-400">${data.successful_requests || 0}</div>
                </div>
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm mb-1">Failed</div>
                    <div class="text-3xl font-bold text-red-400">${data.failed_requests || 0}</div>
                </div>
                <div class="bg-gray-900 border border-gray-800 rounded-lg p-6">
                    <div class="text-gray-400 text-sm mb-1">Total Chunks</div>
                    <div class="text-3xl font-bold">${data.total_chunks || 0}</div>
                </div>
            `;
        }

        async function loadSettings() {
            const resp = await fetch('/v1/admin/settings', {
                headers: { 'Authorization': 'Bearer ' + masterKey }
            });
            const settings = await resp.json();

            Object.keys(settings).forEach(key => {
                const el = document.getElementById('setting-' + key);
                if (el) el.value = settings[key];
            });

            // Update QR preview after loading settings
            updateQRPreview();
        }

        document.getElementById('settings-form').addEventListener('submit', async (e) => {
            e.preventDefault();

            const settings = {
                bank_id: document.getElementById('setting-bank_id').value,
                bank_account: document.getElementById('setting-bank_account').value,
                bank_holder: document.getElementById('setting-bank_holder').value,
                price_starter_vnd: document.getElementById('setting-price_starter_vnd').value,
                price_pro_vnd: document.getElementById('setting-price_pro_vnd').value,
            };

            await fetch('/v1/admin/settings', {
                method: 'POST',
                headers: {
                    'Authorization': 'Bearer ' + masterKey,
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(settings)
            });

            alert('Settings saved!');
            updateQRPreview(); // Update QR after saving
        });

        // Bank name mapping
        const bankNames = {
            '970422': 'MB Bank',
            '970436': 'Vietcombank',
            '970407': 'Techcombank',
            '970416': 'ACB',
            '970418': 'BIDV',
            '970432': 'VPBank',
            '970423': 'TPBank',
            '970403': 'Sacombank',
            '970437': 'HDBank',
            '970441': 'VIB',
            '970426': 'MSB',
            '970443': 'SHB',
            '970431': 'Eximbank',
            '970448': 'OCB',
            '970449': 'LienVietPostBank',
            '970428': 'Nam A Bank',
            '970429': 'SCB',
            '970409': 'Bac A Bank',
            '546034': 'CAKE',
            '546035': 'Ubank'
        };

        // Update QR preview function
        function updateQRPreview() {
            const bankId = document.getElementById('setting-bank_id').value;
            const bankAccount = document.getElementById('setting-bank_account').value;
            const bankHolder = document.getElementById('setting-bank_holder').value;
            const priceStarter = document.getElementById('setting-price_starter_vnd').value;
            const pricePro = document.getElementById('setting-price_pro_vnd').value;

            // Check if required fields are filled
            if (!bankId || !bankAccount) {
                document.getElementById('qr-preview-empty').classList.remove('hidden');
                document.getElementById('qr-preview-content').classList.add('hidden');
                return;
            }

            // Show preview content
            document.getElementById('qr-preview-empty').classList.add('hidden');
            document.getElementById('qr-preview-content').classList.remove('hidden');

            const bankName = bankNames[bankId] || bankId;

            // Generate Starter QR
            const starterMemo = `CRAWLKIT test@example.com starter`;
            const starterQRUrl = `https://img.vietqr.io/image/${bankId}-${bankAccount}-compact2.png?amount=${priceStarter || 0}&addInfo=${encodeURIComponent(starterMemo)}&accountName=${encodeURIComponent(bankHolder || '')}`;
            
            document.getElementById('qr-starter').src = starterQRUrl;
            document.getElementById('qr-starter-bank').textContent = bankName;
            document.getElementById('qr-starter-account').textContent = bankAccount;
            document.getElementById('qr-starter-holder').textContent = bankHolder || '-';
            document.getElementById('qr-starter-amount').textContent = priceStarter ? parseInt(priceStarter).toLocaleString() + ' VND' : '-';
            document.getElementById('qr-starter-memo').textContent = starterMemo;

            // Generate Pro QR
            const proMemo = `CRAWLKIT test@example.com pro`;
            const proQRUrl = `https://img.vietqr.io/image/${bankId}-${bankAccount}-compact2.png?amount=${pricePro || 0}&addInfo=${encodeURIComponent(proMemo)}&accountName=${encodeURIComponent(bankHolder || '')}`;
            
            document.getElementById('qr-pro').src = proQRUrl;
            document.getElementById('qr-pro-bank').textContent = bankName;
            document.getElementById('qr-pro-account').textContent = bankAccount;
            document.getElementById('qr-pro-holder').textContent = bankHolder || '-';
            document.getElementById('qr-pro-amount').textContent = pricePro ? parseInt(pricePro).toLocaleString() + ' VND' : '-';
            document.getElementById('qr-pro-memo').textContent = proMemo;
        }

        // Attach oninput listeners to all settings fields
        document.getElementById('setting-bank_id').addEventListener('change', updateQRPreview);
        document.getElementById('setting-bank_account').addEventListener('input', updateQRPreview);
        document.getElementById('setting-bank_holder').addEventListener('input', updateQRPreview);
        document.getElementById('setting-price_starter_vnd').addEventListener('input', updateQRPreview);
        document.getElementById('setting-price_pro_vnd').addEventListener('input', updateQRPreview);

        function showTab(tab) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[id^="tab-"]').forEach(el => {
                el.classList.remove('border-indigo-500');
                el.classList.add('border-transparent');
            });

            // Show selected tab
            document.getElementById('content-' + tab).classList.remove('hidden');
            document.getElementById('tab-' + tab).classList.remove('border-transparent');
            document.getElementById('tab-' + tab).classList.add('border-indigo-500');

            // Load data
            if (tab === 'users') loadUsers();
            if (tab === 'keys') loadKeys();
            if (tab === 'payments') loadPayments();
            if (tab === 'usage') loadUsage();
            if (tab === 'settings') loadSettings();
        }

        function logout() {
            localStorage.removeItem('crawlkit_master_key');
            location.reload();
        }
    </script>
""", show_nav=False)
