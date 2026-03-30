# Filecoin Improvement Proposals (FIPs) Dashboard

🔗 **Live Dashboard: [tanisha-katara.github.io/fips-dashboard](https://tanisha-katara.github.io/fips-dashboard/)**

A real-time dashboard tracking the status of all Filecoin Improvement Proposals (FIPs), including month-on-month status changes and open pull requests.

## Features

- 📊 **Current Status Table**: View all FIPs organized by status
- 📅 **Timeline Tracker**: Month-on-month status change tracking
- 🔀 **Open PRs**: See all open pull requests related to FIPs
- 🔄 **Auto-Update**: Automatically refreshes with latest data

## Files

- `fips-dashboard-static.html` - Main dashboard with current FIP statuses and PRs
- `fips-timeline-tracker.html` - Timeline view showing status changes over time
- `generate_fips_dashboard.py` - Script to generate the main dashboard
- `fips_timeline_tracker.py` - Script to generate the timeline tracker
- `fetch_fip_prs.py` - Script to fetch and analyze open PRs

## Usage

### Generate Dashboard Locally

```bash
# Generate main dashboard
python3 generate_fips_dashboard.py

# Generate timeline tracker
python3 fips_timeline_tracker.py

# Open in browser
open fips-dashboard-static.html
```

### View Locally

```bash
python3 -m http.server 8000
# Then visit http://localhost:8000/fips-dashboard-static.html
```

## Publishing

See [PUBLISHING_GUIDE.md](PUBLISHING_GUIDE.md) for detailed instructions on publishing to:
- GitHub Pages (recommended)
- Netlify
- Vercel
- Other hosting services

## Auto-Update Setup

The included GitHub Actions workflow (`.github/workflows/update-dashboard.yml`) will automatically update the dashboard every 6 hours.

To enable:
1. Push this repository to GitHub
2. Enable GitHub Actions in repository settings
3. The dashboard will auto-update!

## License

This dashboard is provided as-is for tracking Filecoin Improvement Proposals.
