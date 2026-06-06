# PH Job Market Tracker — React Frontend

A professional job search dashboard for the Philippine job market, built with Vite + React 18 + TailwindCSS + Recharts.

## Quick Start

### Prerequisites
- Node.js 18+
- Django API running on `http://localhost:8000` (see `/api` folder)

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Starts the Vite dev server on `http://localhost:5173`. The server is configured to proxy API calls to `http://localhost:8000`.

### Production Build

```bash
npm run build
```

Outputs optimized production files to `dist/`.

## Project Structure

```
frontend/
├── src/
│   ├── main.jsx              # React entry point
│   ├── App.jsx               # Router setup
│   ├── api/
│   │   └── client.js         # Axios API client
│   ├── components/
│   │   ├── Header.jsx        # Navigation header
│   │   └── Badge.jsx         # UI badges (source, employment type, remote)
│   ├── pages/
│   │   ├── JobsPage.jsx      # Job search + filters + results + pagination
│   │   └── DashboardPage.jsx # Analytics dashboard with Recharts
│   └── styles/
│       └── index.css         # Global styles + design tokens
├── index.html                # Entry HTML with font imports
├── vite.config.js            # Vite configuration
├── tailwind.config.js        # TailwindCSS configuration
└── package.json              # Dependencies
```

## Features

### Jobs Page (/)
- **Search**: Full-text search across job title, company, location
- **Filters**: 
  - Salary range (min/max in PHP)
  - Employment type (full-time, part-time, contract, freelance, temporary)
  - Location (city/province dropdown)
  - Company (dropdown)
  - Source (philjobnet, kalibrr, jobstreet, onlinejobs, indeed, facebook)
  - Remote toggle
- **Sort**: By newest, highest salary, company name
- **Results**: Full-width cards with title, company, location, salary, source badge, date
- **Pagination**: 25 results per page
- **Detail Drawer**: Click any job to view full details + apply link

### Dashboard (/dashboard)
- **Summary Cards**: Total jobs, average salary, max salary, top location, top company
- **Charts**:
  - Salary by Location (bar chart)
  - Jobs by Source (pie chart)
  - Remote vs Onsite (donut chart)
  - Salary by Experience Level (bar chart)
  - Top 10 Skills in Demand (bar chart)

All charts are fully responsive and built with Recharts.

## API Integration

The frontend consumes the Django REST API at `/api/v1/`. See `src/api/client.js` for all endpoints.

### Environment

Set the API URL via `.env`:

```
VITE_API_URL=http://localhost:8000
```

The dev server proxies all `/api` requests to this URL automatically.

## Design System

**Fonts:**
- UI: Hanken Grotesk (primary)
- Data/badges: IBM Plex Mono (monospace)

**Colors:**
- Accent: Customizable hue (default `oklch(0.55 0.17 250)` — blue)
- Palette: Cool-neutral (grays with cool undertones)
- No gradients, minimal shadows, thin 1px borders

**Spacing & Sizing:**
- Card padding: 20px (compact mode: 15px)
- Row gap: 14px (compact: 9px)
- Border radius: 9px (cards), 6px (buttons)

## Testing

Manual testing checklist:

1. Start Django: `python api/manage.py runserver` (from `api/` folder)
2. Start frontend: `npm run dev`
3. Open http://localhost:5173
4. **Jobs page**:
   - Search for a job title
   - Filter by salary range, location, company
   - Click a job to see details
   - Navigate pages
5. **Dashboard**:
   - Verify all charts render
   - Check data aligns with API responses

## Performance

- Production build: ~625KB gzipped
- Chart library: Recharts (lightweight, React-native)
- No external image dependencies
- Vite dev server: instant HMR

## Known Limitations

- No auth/login (read-only public API)
- Charts filter to well-sampled cities (≥8 jobs) for statistical stability
- Facebook jobs optional (requires manual setup in scraper)

## Next Steps

- Add unit/integration tests
- Implement design tweaks panel (accent color, card style variations)
- Deploy to production server
- Add job posting detail as its own route
