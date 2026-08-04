# Publishing Guide for FIPs Dashboard

This guide covers multiple ways to publish your FIPs dashboard.

## Option 1: GitHub Pages (Recommended - Free & Easy)

### Step 1: Create a GitHub Repository

1. Go to [GitHub](https://github.com) and create a new repository (e.g., `fips-dashboard`)
2. Make sure it's set to **Public** (required for free GitHub Pages)

### Step 2: Upload Files

You can either use GitHub's web interface or Git:

**Using Git (Command Line):**
```bash
cd /path/to/your/project
git init
git add fips-dashboard-static.html fips-timeline-tracker.html generate_fips_dashboard.py fips_timeline_tracker.py fetch_fip_prs.py
git commit -m "Initial commit: FIPs dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/fips-dashboard.git
git push -u origin main
```

**Using GitHub Web Interface:**
1. Go to your repository
2. Click "Add file" → "Upload files"
3. Upload all the HTML files and Python scripts

### Step 3: Enable GitHub Pages

1. Go to your repository settings
2. Scroll to "Pages" section
3. Under "Source", select "Deploy from a branch"
4. Choose branch: `main`
5. Choose folder: `/ (root)`
6. Click "Save"

Your dashboard will be available at:
`https://YOUR_USERNAME.github.io/fips-dashboard/fips-dashboard-static.html`

### Step 4: Set Up Auto-Update (Optional)

Create a GitHub Actions workflow to automatically update the dashboard daily:

Create `.github/workflows/update-dashboard.yml`:

```yaml
name: Update FIPs Dashboard

on:
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours
  workflow_dispatch:  # Manual trigger

jobs:
  update:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.x'
      
      - name: Generate Dashboard
        run: |
          python3 generate_fips_dashboard.py
          python3 fips_timeline_tracker.py
      
      - name: Commit and Push
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add *.html
          git commit -m "Auto-update dashboard $(date +'%Y-%m-%d %H:%M:%S')" || exit 0
          git push
```

---

## Option 2: Netlify (Free & Easy)

### Step 1: Sign Up
1. Go to [Netlify](https://www.netlify.com)
2. Sign up with GitHub

### Step 2: Deploy
1. Click "Add new site" → "Deploy manually"
2. Drag and drop your HTML files
3. Your site will be live immediately!

### Step 3: Auto-Deploy (Optional)
1. Connect your GitHub repository
2. Netlify will auto-deploy on every push

---

## Option 3: Vercel (Free & Easy)

### Step 1: Sign Up
1. Go to [Vercel](https://vercel.com)
2. Sign up with GitHub

### Step 2: Deploy
1. Click "New Project"
2. Import your GitHub repository
3. Vercel will auto-detect and deploy

---

## Option 4: Simple Static Hosting

### Using Python's Built-in Server (Local Testing)
```bash
cd /Users/tanishakatara
python3 -m http.server 8000
```
Then visit: `http://localhost:8000/fips-dashboard-static.html`

### Using Any Web Hosting Service
- Upload the HTML files to any web hosting service
- Most hosting providers support static HTML files
- Examples: Bluehost, HostGator, AWS S3, Google Cloud Storage

---

## Quick Setup Script for GitHub Pages

Run this script to set up everything automatically:

```bash
#!/bin/bash
# setup-github-pages.sh

REPO_NAME="fips-dashboard"
GITHUB_USERNAME="YOUR_USERNAME"  # Change this!

# Initialize git repo
git init
git add *.html *.py
git commit -m "Initial commit: FIPs dashboard"

# Create GitHub repo and push
gh repo create $REPO_NAME --public --source=. --remote=origin --push

# Enable GitHub Pages (requires GitHub CLI)
gh api repos/$GITHUB_USERNAME/$REPO_NAME/pages \
  --method POST \
  -f source[type]=branch \
  -f source[branch]=main \
  -f source[path]=/

echo "Dashboard will be available at: https://$GITHUB_USERNAME.github.io/$REPO_NAME/fips-dashboard-static.html"
```

---

## Recommended: GitHub Pages with Auto-Update

This is the best option because:
- ✅ Free
- ✅ Automatic updates via GitHub Actions
- ✅ Easy to share (just share the URL)
- ✅ Version controlled
- ✅ No server maintenance needed

Your dashboard will automatically update every 6 hours with the latest FIP data!
