# CrawlKit Frontend

Modern, professional SaaS frontend for CrawlKit API.

## Features

- 🎨 Dark theme with Tailwind CSS
- 📱 Fully responsive (mobile-first)
- 🔐 User authentication & dashboard
- 💳 VietQR payment integration
- 👨‍💼 Admin panel with full management
- 📊 Usage statistics & analytics
- 🚀 Optimized for Vercel deployment

## Structure

```
crawlkit-web/
├── index.html          # Landing page
├── signup.html         # Registration
├── login.html          # Login
├── dashboard.html      # User dashboard
├── admin.html          # Admin panel
├── css/
│   └── style.css       # Shared styles
├── js/
│   ├── config.js       # API configuration
│   ├── auth.js         # Auth utilities
│   ├── dashboard.js    # Dashboard logic
│   └── admin.js        # Admin logic
├── vercel.json         # Vercel config
└── package.json        # Project metadata
```

## Local Development

```bash
# Serve with Python
python3 -m http.server 8000

# Or use any static server
npx serve
```

Then open http://localhost:8000

## Deployment to Vercel

1. Install Vercel CLI: `npm i -g vercel`
2. Login: `vercel login`
3. Deploy: `vercel --prod`

Or connect your Git repo to Vercel for automatic deployments.

## API Backend

Backend URL: `https://api.crawlkit.org`

Configure in `js/config.js` if needed.

## Environment

No environment variables needed for frontend. All configuration is in `js/config.js`.

## Tech Stack

- **Styling**: Tailwind CSS (via CDN)
- **Charts**: Chart.js (for usage graphs)
- **Deployment**: Vercel
- **Backend**: Railway (API server)

## Features

### Landing Page
- Hero section with CTA
- Features showcase
- Pricing cards
- Code examples
- Footer

### Dashboard
- Overview with stats
- API key management
- Usage analytics
- Plan upgrades with VietQR
- Documentation

### Admin Panel
- User management
- API key control
- Payment confirmations
- System statistics
- Bank settings & QR preview

## License

MIT
