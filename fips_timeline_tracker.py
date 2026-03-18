#!/usr/bin/env python3
"""
Script to track FIP status changes month-on-month using GitHub commit history
"""

import urllib.request
import json
import re
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from fip_utils import get_status_class, parse_fip_table

GITHUB_API_BASE = 'https://api.github.com/repos/filecoin-project/FIPs'
README_PATH = 'README.md'

def fetch_commits_since_date(since_date: str = None):
    """Fetch commits to README.md since a given date"""
    url = f"{GITHUB_API_BASE}/commits?path={README_PATH}&per_page=100"
    if since_date:
        url += f"&since={since_date}"
    
    try:
        with urllib.request.urlopen(url) as response:
            commits = json.loads(response.read().decode('utf-8'))
            return commits
    except Exception as e:
        print(f"Error fetching commits: {e}")
        return []

def get_readme_at_commit(sha: str):
    """Get README content at a specific commit"""
    url = f"{GITHUB_API_BASE}/contents/{README_PATH}?ref={sha}"
    try:
        with urllib.request.urlopen(url) as response:
            content = json.loads(response.read().decode('utf-8'))
            import base64
            return base64.b64decode(content['content']).decode('utf-8')
    except Exception as e:
        print(f"Error fetching README at commit {sha}: {e}")
        return None

def parse_fips_from_text(text: str):
    """Parse FIPs from README text, returning a dict keyed by FIP number."""
    return {fip['number']: fip for fip in parse_fip_table(text)}

def get_monthly_snapshots():
    """Get monthly snapshots of FIP statuses"""
    # Get commits from the last 12 months
    since_date = (datetime.now() - timedelta(days=365)).isoformat()
    commits = fetch_commits_since_date(since_date)
    
    if not commits:
        print("No commits found, fetching current version...")
        # Fallback: just get current version
        try:
            with urllib.request.urlopen(f"https://raw.githubusercontent.com/filecoin-project/FIPs/master/{README_PATH}") as response:
                text = response.read().decode('utf-8')
                fips = parse_fips_from_text(text)
                return {datetime.now().strftime('%Y-%m'): fips}
        except Exception as e:
            print(f"Error: {e}")
            return {}
    
    # Group commits by month
    monthly_commits = defaultdict(list)
    for commit in commits:
        commit_date = datetime.fromisoformat(commit['commit']['committer']['date'].replace('Z', '+00:00'))
        month_key = commit_date.strftime('%Y-%m')
        monthly_commits[month_key].append({
            'sha': commit['sha'],
            'date': commit_date,
            'message': commit['commit']['message']
        })
    
    # For each month, get the latest commit's README
    monthly_snapshots = {}
    for month, month_commits in sorted(monthly_commits.items()):
        # Use the latest commit of the month
        latest_commit = max(month_commits, key=lambda x: x['date'])
        print(f"Fetching snapshot for {month} (commit {latest_commit['sha'][:7]})...")
        
        readme_text = get_readme_at_commit(latest_commit['sha'])
        if readme_text:
            fips = parse_fips_from_text(readme_text)
            monthly_snapshots[month] = {
                'fips': fips,
                'date': latest_commit['date'],
                'commit': latest_commit['sha'][:7]
            }
    
    # Also get current version
    try:
        with urllib.request.urlopen(f"https://raw.githubusercontent.com/filecoin-project/FIPs/master/{README_PATH}") as response:
            text = response.read().decode('utf-8')
            fips = parse_fips_from_text(text)
            current_month = datetime.now().strftime('%Y-%m')
            if current_month not in monthly_snapshots:
                monthly_snapshots[current_month] = {
                    'fips': fips,
                    'date': datetime.now(),
                    'commit': 'HEAD'
                }
    except Exception as e:
        print(f"Error fetching current version: {e}")
    
    return monthly_snapshots

def track_status_changes(monthly_snapshots: Dict):
    """Track status changes between months"""
    changes = []
    sorted_months = sorted(monthly_snapshots.keys())
    
    for i in range(len(sorted_months)):
        month = sorted_months[i]
        fips = monthly_snapshots[month]['fips']
        
        if i == 0:
            # First month - all FIPs are "new" or initial status
            continue
        
        prev_month = sorted_months[i-1]
        prev_fips = monthly_snapshots[prev_month]['fips']
        
        month_changes = {
            'month': month,
            'date': monthly_snapshots[month]['date'],
            'new_fips': [],
            'status_changes': [],
            'removed_fips': []
        }
        
        # Check for new FIPs
        for fip_num, fip_data in fips.items():
            if fip_num not in prev_fips:
                month_changes['new_fips'].append({
                    'number': fip_num,
                    'title': fip_data['title'],
                    'status': fip_data['status']
                })
            elif prev_fips[fip_num]['status'] != fip_data['status']:
                month_changes['status_changes'].append({
                    'number': fip_num,
                    'title': fip_data['title'],
                    'from': prev_fips[fip_num]['status'],
                    'to': fip_data['status']
                })
        
        # Check for removed FIPs (shouldn't happen, but track anyway)
        for fip_num in prev_fips:
            if fip_num not in fips:
                month_changes['removed_fips'].append({
                    'number': fip_num,
                    'title': prev_fips[fip_num]['title'],
                    'status': prev_fips[fip_num]['status']
                })
        
        if month_changes['new_fips'] or month_changes['status_changes'] or month_changes['removed_fips']:
            changes.append(month_changes)
    
    return changes, sorted_months

def generate_timeline_html(monthly_snapshots: Dict, changes: List, sorted_months: List):
    """Generate HTML dashboard with timeline view"""
    
    # Generate timeline HTML
    timeline_html = []
    for change in changes:
        month_date = change['date'].strftime('%B %Y') if isinstance(change['date'], datetime) else change['month']
        
        change_items = []
        
        if change['new_fips']:
            for fip in change['new_fips']:
                change_items.append(f'''
                    <div class="change-item new">
                        <span class="change-icon">➕</span>
                        <span class="change-text">
                            <strong>New:</strong> <a href="https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-{fip['number']}.md" target="_blank">FIP-{fip['number']}</a> - {fip['title'][:60]}...
                            <span class="status-badge {get_status_class(fip['status'])}">{fip['status']}</span>
                        </span>
                    </div>''')
        
        if change['status_changes']:
            for fip in change['status_changes']:
                change_items.append(f'''
                    <div class="change-item status-change">
                        <span class="change-icon">🔄</span>
                        <span class="change-text">
                            <strong>Status Change:</strong> <a href="https://github.com/filecoin-project/FIPs/blob/master/FIPS/fip-{fip['number']}.md" target="_blank">FIP-{fip['number']}</a> - {fip['title'][:50]}...
                            <span class="status-change-arrow">{fip['from']} → {fip['to']}</span>
                        </span>
                    </div>''')
        
        if change['removed_fips']:
            for fip in change['removed_fips']:
                change_items.append(f'''
                    <div class="change-item removed">
                        <span class="change-icon">➖</span>
                        <span class="change-text">
                            <strong>Removed:</strong> FIP-{fip['number']} - {fip['title'][:60]}...
                        </span>
                    </div>''')
        
        if change_items:
            timeline_html.append(f'''
                <div class="timeline-month">
                    <div class="timeline-header">
                        <h3>{month_date}</h3>
                        <span class="change-count">{len(change['new_fips']) + len(change['status_changes']) + len(change['removed_fips'])} changes</span>
                    </div>
                    <div class="timeline-changes">
                        {''.join(change_items)}
                    </div>
                </div>''')
    
    # Generate current status summary
    current_month = sorted_months[-1] if sorted_months else datetime.now().strftime('%Y-%m')
    current_fips = monthly_snapshots[current_month]['fips'] if current_month in monthly_snapshots else {}
    
    status_summary = defaultdict(int)
    for fip in current_fips.values():
        status_summary[fip['status']] += 1
    
    summary_html = '<div class="status-summary-grid">'
    for status, count in sorted(status_summary.items(), key=lambda x: x[1], reverse=True):
        summary_html += f'''
            <div class="summary-card">
                <div class="summary-status {get_status_class(status)}">{status}</div>
                <div class="summary-count">{count}</div>
            </div>'''
    summary_html += '</div>'
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FIP Status Timeline Tracker</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}

        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 12px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }}

        .header {{
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}

        .header h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
        }}

        .header p {{
            opacity: 0.9;
            font-size: 1.1em;
        }}

        .content {{
            padding: 30px;
        }}

        .section {{
            margin-bottom: 40px;
        }}

        .section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}

        .status-summary-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}

        .summary-card {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 2px solid #e0e0e0;
        }}

        .summary-status {{
            font-size: 0.85em;
            font-weight: 600;
            margin-bottom: 8px;
            padding: 4px 8px;
            border-radius: 4px;
            display: inline-block;
        }}

        .summary-count {{
            font-size: 2em;
            font-weight: 700;
            color: #667eea;
        }}

        .timeline {{
            position: relative;
            padding-left: 30px;
        }}

        .timeline::before {{
            content: '';
            position: absolute;
            left: 10px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #667eea;
        }}

        .timeline-month {{
            position: relative;
            margin-bottom: 30px;
            padding-left: 30px;
        }}

        .timeline-month::before {{
            content: '';
            position: absolute;
            left: 2px;
            top: 10px;
            width: 16px;
            height: 16px;
            border-radius: 50%;
            background: #667eea;
            border: 3px solid white;
            box-shadow: 0 0 0 2px #667eea;
        }}

        .timeline-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}

        .timeline-header h3 {{
            color: #333;
            font-size: 1.4em;
        }}

        .change-count {{
            background: #667eea;
            color: white;
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.9em;
            font-weight: 600;
        }}

        .timeline-changes {{
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }}

        .change-item {{
            padding: 10px;
            margin-bottom: 8px;
            border-radius: 6px;
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }}

        .change-item.new {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}

        .change-item.status-change {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}

        .change-item.removed {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}

        .change-icon {{
            font-size: 1.2em;
        }}

        .change-text {{
            flex: 1;
            line-height: 1.6;
        }}

        .change-text a {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }}

        .change-text a:hover {{
            text-decoration: underline;
        }}

        .status-badge {{
            display: inline-block;
            padding: 4px 8px;
            border-radius: 12px;
            font-size: 0.75em;
            font-weight: 600;
            margin-left: 8px;
        }}

        .status-final {{ background: #d4edda; color: #155724; }}
        .status-draft {{ background: #fff3cd; color: #856404; }}
        .status-accepted {{ background: #cce5ff; color: #004085; }}
        .status-deferred {{ background: #ffeaa7; color: #856404; }}
        .status-rejected {{ background: #f8d7da; color: #721c24; }}
        .status-withdrawn {{ background: #e2e3e5; color: #383d41; }}
        .status-active {{ background: #d1ecf1; color: #0c5460; }}
        .status-last-call {{ background: #f0ad4e; color: #fff; }}
        .status-superseded {{ background: #e7e7e7; color: #555; }}

        .status-change-arrow {{
            display: inline-block;
            margin-left: 8px;
            padding: 2px 8px;
            background: white;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 600;
        }}

        .no-changes {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }}

        .last-updated {{
            text-align: center;
            padding: 20px;
            color: #666;
            font-size: 0.9em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📅 FIP Status Timeline Tracker</h1>
            <p>Month-on-Month Status Change Tracking</p>
        </div>

        <div class="content">
            <div class="section">
                <h2>Current Status Summary</h2>
                {summary_html}
            </div>

            <div class="section">
                <h2>Status Changes Timeline</h2>
                <div class="timeline">
                    {''.join(timeline_html) if timeline_html else '<div class="no-changes">No status changes tracked yet. Historical data will appear here as FIPs change status over time.</div>'}
                </div>
            </div>
        </div>

        <div class="last-updated">
            Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
    </div>
</body>
</html>'''
    
    return html

def main():
    print("Fetching monthly snapshots from GitHub...")
    monthly_snapshots = get_monthly_snapshots()
    
    if not monthly_snapshots:
        print("Failed to fetch snapshots")
        return
    
    print(f"Found snapshots for {len(monthly_snapshots)} month(s)")
    
    print("Tracking status changes...")
    changes, sorted_months = track_status_changes(monthly_snapshots)
    
    print(f"Found {len(changes)} months with changes")
    
    print("Generating timeline HTML...")
    html = generate_timeline_html(monthly_snapshots, changes, sorted_months)
    
    output_file = 'fips-timeline-tracker.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Timeline tracker generated successfully: {output_file}")
    print(f"Open {output_file} in your browser to view the timeline")

if __name__ == '__main__':
    main()