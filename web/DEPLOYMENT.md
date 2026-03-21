# Deployment Guide for CrawlKit Frontend

## ✅ Project Complete

All files have been created and committed to git repository at:
`/home/node/.openclaw/workspace/crawlkit-web/`

## 📦 What's Included

### HTML Pages
- ✅ `index.html` - Landing page with hero, features, pricing, code examples
- ✅ `signup.html` - User registration form
- ✅ `login.html` - User login form
- ✅ `dashboard.html` - User dashboard with API key management, usage stats, upgrade
- ✅ `admin.html` - Admin panel with full management features

### Assets
- ✅ `css/style.css` - Custom styles (only plain CSS, no @apply)
- ✅ `js/config.js` - API URL configuration
- ✅ `js/auth.js` - Authentication utilities
- ✅ `js/dashboard.js` - Dashboard logic
- ✅ `js/admin.js` - Admin panel logic

### Configuration
- ✅ `vercel.json` - Vercel deployment config (rewrites, headers)
- ✅ `package.json` - Project metadata
- ✅ `.gitignore` - Git ignore rules
- ✅ `README.md` - Project documentation

### Git
- ✅ Repository initialized
- ✅ All files committed
- ⚠️ **Not pushed** (as requested)

## 🚀 Deploy to Vercel

### Option 1: Vercel CLI (Recommended)

```bash
cd /home/node/.openclaw/workspace/crawlkit-web

# Install Vercel CLI (if not installed)
npm i -g vercel

# Login
vercel login

# Deploy
vercel --prod
```

### Option 2: Git + Vercel Dashboard

1. Create a new repository on GitHub
2. Push the code:
   ```bash
   cd /home/node/.openclaw/workspace/crawlkit-web
   git remote add origin https://github.com/YOUR_USERNAME/crawlkit-web.git
   git push -u origin master
   ```
3. Go to [vercel.com](https://vercel.com)
4. Click "New Project"
5. Import your GitHub repository
6. Vercel will auto-detect the configuration
7. Click "Deploy"

### Option 3: Drag & Drop

1. Zip the project folder (exclude `.git/`)
2. Go to [vercel.com](https://vercel.com)
3. Drag and drop the zip file

## 🔧 Configuration

### API Backend
Backend URL is configured in `js/config.js`:
```javascript
const API_URL = 'https://api.crawlkit.org';
```

### CORS
Make sure your Railway backend allows requests from your Vercel domain. Add to backend's CORS settings:
```
https://your-project.vercel.app
```

## ✨ Features

### Landing Page
- Hero section with value proposition
- Features showcase (4 cards)
- Supported sites badges
- Pricing (4 plans: Free, Starter, Pro, Enterprise)
- Code examples (cURL, Python, JavaScript)
- Footer with links

### Authentication
- Signup form with validation
- Login form
- LocalStorage-based auth
- Auto-redirect on successful login

### Dashboard
**Sidebar Navigation:**
- Overview
- API Keys
- Usage
- Upgrade Plan
- Docs

**Features:**
- Real-time stats (total, today, month, rate limit)
- API key management (reveal, copy, create, revoke)
- Usage chart (Chart.js)
- Recent requests table
- VietQR payment integration
- Plan upgrade flow
- API documentation

### Admin Panel
**Master Key Authentication:**
- Secure admin login
- LocalStorage session

**Tabs:**
1. **Users** - List all users, search, view details
2. **API Keys** - List all keys, enable/disable
3. **Payments** - Pending confirmations, confirm/reject
4. **Usage** - System-wide statistics
5. **Settings**:
   - Bank dropdown (21 Vietnamese banks)
   - Account configuration
   - Pricing setup
   - Live QR preview

## 🎨 Design

- **Theme**: Dark mode (gray-950 bg, gray-900 cards, indigo-600 accent)
- **Styling**: Tailwind CSS via CDN (utility classes only)
- **Responsive**: Mobile-first design
- **Charts**: Chart.js for analytics
- **Icons**: Emoji-based (🕷️ 🔑 📊 etc.)

## 🔒 Security

- X-Frame-Options header set to DENY
- X-Content-Type-Options set to nosniff
- Referrer-Policy set to strict-origin-when-cross-origin
- Master key required for admin access
- API keys masked by default

## 📝 API Endpoints Expected

The frontend expects these backend endpoints:

**Auth:**
- POST `/v1/auth/register` - User registration
- POST `/v1/auth/login` - User login

**User:**
- GET `/v1/stats` - User statistics
- GET `/v1/keys` - User's API keys
- POST `/v1/keys` - Create new key
- DELETE `/v1/keys/:id` - Revoke key
- GET `/v1/usage` - Usage data with chart
- GET `/v1/payment/settings` - Public payment settings
- POST `/v1/payment/request` - Submit payment request

**Admin:**
- POST `/v1/admin/verify` - Verify master key
- GET `/v1/admin/users` - List all users
- GET `/v1/admin/keys` - List all API keys
- POST `/v1/admin/keys/:id/toggle` - Enable/disable key
- GET `/v1/admin/payments` - List pending payments
- POST `/v1/admin/payments/:id/confirm` - Confirm payment
- POST `/v1/admin/payments/:id/reject` - Reject payment
- GET `/v1/admin/stats` - System statistics
- GET `/v1/admin/settings` - Get settings
- POST `/v1/admin/settings` - Update settings
- GET `/v1/admin/settings/public` - Public settings (for QR)

## 🧪 Testing Locally

```bash
cd /home/node/.openclaw/workspace/crawlkit-web

# Python server
python3 -m http.server 8000

# Or Node.js
npx serve

# Or PHP
php -S localhost:8000
```

Then open http://localhost:8000

## 📌 Next Steps

1. ✅ Project is complete and committed
2. 🔄 Connect to Vercel (manual step by Bi)
3. 🔄 Configure backend CORS for Vercel domain
4. 🔄 Test all flows (signup, login, dashboard, payments, admin)
5. 🔄 Add real payment bank details in admin settings

## 🐛 Known Considerations

- Backend API must implement all expected endpoints
- CORS must allow frontend domain
- VietQR requires valid Vietnamese bank details
- Chart.js loads from CDN (requires internet)
- LocalStorage used for auth (client-side only)

## 📞 Support

For issues or questions:
- Check `README.md` for documentation
- Review `DEPLOYMENT.md` for deployment steps
- Contact: dev@crawlkit.dev

---

**Status**: ✅ Ready for deployment to Vercel
**Commit**: `c63007f Initial commit: Complete CrawlKit frontend`
**Date**: 2026-03-19
