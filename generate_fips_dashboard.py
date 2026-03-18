#!/usr/bin/env python3
"""
Script to generate a static FIPs dashboard HTML file
"""

import urllib.request
import json
import re
from collections import defaultdict
from datetime import datetime
from fip_utils import get_status_class, parse_fip_table

FIPS_REPO_URL = 'https://raw.githubusercontent.com/filecoin-project/FIPs/master/README.md'
FIPS_BASE_URL = 'https://github.com/filecoin-project/FIPs/blob/master/'
GITHUB_API_BASE = 'https://api.github.com/repos/filecoin-project/FIPs'

def fetch_readme():
    """Fetch the README from GitHub"""
    try:
        with urllib.request.urlopen(FIPS_REPO_URL) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error fetching README: {e}")
        return None

def parse_fips(text):
    """Parse FIPs from the README markdown"""
    return parse_fip_table(text)

def fetch_open_prs():
    """Fetch all open pull requests"""
    url = f"{GITHUB_API_BASE}/pulls?state=open&per_page=100"
    try:
        with urllib.request.urlopen(url) as response:
            prs = json.loads(response.read().decode('utf-8'))
            return prs
    except Exception as e:
        print(f"Warning: Could not fetch PRs: {e}")
        return []

def extract_fip_numbers(text):
    """Extract FIP numbers from PR title, body, or branch name"""
    fip_numbers = set()
    patterns = [
        r'FIP[-\s]?(\d{4})',
        r'fip[-\s]?(\d{4})',
        r'\[(\d{4})\]',
        r'#(\d{4})',
    ]
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        for match in matches:
            fip_numbers.add(match.zfill(4))
    return sorted(list(fip_numbers))

def process_prs(prs):
    """Process PRs and extract FIP information"""
    fip_prs = {}
    for pr in prs:
        title = pr.get('title', '')
        body = pr.get('body', '')
        branch = pr.get('head', {}).get('ref', '')
        search_text = f"{title} {body} {branch}"
        fip_numbers = extract_fip_numbers(search_text)
        
        pr_info = {
            'number': pr.get('number'),
            'title': title,
            'url': pr.get('html_url'),
            'author': pr.get('user', {}).get('login', 'Unknown'),
            'created_at': pr.get('created_at', ''),
        }
        
        for fip_num in fip_numbers:
            if fip_num not in fip_prs:
                fip_prs[fip_num] = []
            fip_prs[fip_num].append(pr_info)
    
    return fip_prs

def generate_prs_section_html(fip_prs):
    """Generate HTML for PRs section"""
    if not fip_prs:
        return '<div class="no-prs">No open PRs found.</div>'
    
    # Get all unique PRs
    all_prs = []
    seen_prs = set()
    for fip_num, prs in fip_prs.items():
        for pr in prs:
            if pr['number'] not in seen_prs:
                all_prs.append((fip_num, pr))
                seen_prs.add(pr['number'])
    
    if not all_prs:
        return '<div class="no-prs">No open PRs found.</div>'
    
    # Group by FIP
    html = '<div class="prs-section">'
    html += f'<h2>Open Pull Requests ({len(seen_prs)} total)</h2>'
    
    # Sort FIPs with PRs
    sorted_fips = sorted(fip_prs.keys())
    
    for fip_num in sorted_fips:
        prs = fip_prs[fip_num]
        html += f'<div class="fip-pr-group">'
        html += f'<div class="fip-pr-header"><strong>FIP-{fip_num}</strong> <span class="pr-count">({len(prs)} PR{"s" if len(prs) > 1 else ""})</span></div>'
        html += '<div class="pr-list">'
        for pr in prs:
            created_date = datetime.fromisoformat(pr['created_at'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
            html += f'''
                <div class="pr-item">
                    <a href="{pr['url']}" target="_blank" class="pr-link">#{pr['number']}: {pr['title']}</a>
                    <span class="pr-meta">By @{pr['author']} • {created_date}</span>
                </div>
            '''
        html += '</div></div>'
    
    html += '</div>'
    return html

def generate_html(fips, fip_prs=None):
    """Generate the HTML dashboard"""
    if fip_prs is None:
        fip_prs = {}
    
    # Group FIPs by status
    status_groups = defaultdict(list)
    for fip in fips:
        status = fip['status']
        if 'Superseded' in status:
            status = 'Superseded'
        status_groups[status].append(fip)
    
    # Sort statuses by count
    sorted_statuses = sorted(status_groups.keys(), key=lambda x: len(status_groups[x]), reverse=True)
    
    # Generate table rows
    table_rows = []
    for status in sorted_statuses:
        fips_in_status = sorted(status_groups[status], key=lambda x: int(x['number']))
        status_class = get_status_class(status)
        
        # Generate FIP links (only FIPs, no FRCs)
        fip_links = []
        for fip in fips_in_status:
            fip_path = f"FIPS/fip-{fip['number']}.md"
            url = f"{FIPS_BASE_URL}{fip_path}"
            fip_num = fip['number']
            
            # Check if there are PRs for this FIP
            pr_badges = ''
            if fip_num in fip_prs:
                pr_count = len(fip_prs[fip_num])
                pr_badges = f' <span class="pr-badge-small" title="{pr_count} open PR{"s" if pr_count > 1 else ""}">🔀 {pr_count}</span>'
            
            fip_links.append(f'<a href="{url}" target="_blank" title="{fip["title"]}">FIP-{fip["number"]}</a>{pr_badges}')
        
        fip_links_html = '\n                            '.join(fip_links)
        
        table_rows.append(f'''
                    <tr>
                        <td><span class="status-badge {status_class}">{status}</span></td>
                        <td><span class="count">{len(fips_in_status)}</span></td>
                        <td>
                            <div class="fips-list">
                                {fip_links_html}
                            </div>
                        </td>
                    </tr>''')
    
    # Calculate stats
    total_fips = len(fips)
    final_count = len(status_groups.get('Final', []))
    draft_count = len(status_groups.get('Draft', []))
    active_count = len(status_groups.get('Accepted', [])) + len(status_groups.get('Last Call', []))
    
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Filecoin Improvement Proposals (FIPs) Dashboard</title>
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

        .last-updated {{
            margin-top: 15px;
            font-size: 0.9em;
            opacity: 0.8;
        }}

        .controls {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            justify-content: space-between;
            align-items: center;
            flex-wrap: wrap;
            gap: 15px;
        }}

        .refresh-btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 600;
            transition: all 0.3s;
        }}

        .refresh-btn:hover {{
            background: #5568d3;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}

        .refresh-btn:active {{
            transform: translateY(0);
        }}

        .status-table {{
            width: 100%;
            border-collapse: collapse;
            margin: 0;
        }}

        .status-table thead {{
            background: #f8f9fa;
        }}

        .status-table th {{
            padding: 18px;
            text-align: left;
            font-weight: 600;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            font-size: 1.1em;
        }}

        .status-table td {{
            padding: 18px;
            border-bottom: 1px solid #e0e0e0;
            vertical-align: top;
        }}

        .status-table tbody tr:hover {{
            background: #f8f9fa;
            transition: background 0.2s;
        }}

        .status-badge {{
            display: inline-block;
            padding: 6px 12px;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}

        .status-final {{
            background: #d4edda;
            color: #155724;
        }}

        .status-draft {{
            background: #fff3cd;
            color: #856404;
        }}

        .status-accepted {{
            background: #cce5ff;
            color: #004085;
        }}

        .status-deferred {{
            background: #ffeaa7;
            color: #856404;
        }}

        .status-rejected {{
            background: #f8d7da;
            color: #721c24;
        }}

        .status-withdrawn {{
            background: #e2e3e5;
            color: #383d41;
        }}

        .status-active {{
            background: #d1ecf1;
            color: #0c5460;
        }}

        .status-last-call {{
            background: #f0ad4e;
            color: #fff;
        }}

        .status-superseded {{
            background: #e7e7e7;
            color: #555;
        }}

        .count {{
            font-size: 1.5em;
            font-weight: 700;
            color: #333;
        }}

        .fips-list {{
            margin-top: 10px;
        }}

        .fips-list a {{
            display: inline-block;
            margin: 4px 8px 4px 0;
            padding: 6px 12px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 4px;
            font-size: 0.9em;
            transition: all 0.2s;
        }}

        .fips-list a:hover {{
            background: #5568d3;
            transform: translateY(-1px);
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }}

        .stats-summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            padding: 30px;
            background: #f8f9fa;
        }}

        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            text-align: center;
        }}

        .stat-card h3 {{
            color: #666;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}

        .stat-card .number {{
            font-size: 2.5em;
            font-weight: 700;
            color: #667eea;
        }}

        .pr-badge-small {{
            display: inline-block;
            background: #28a745;
            color: white;
            font-size: 0.75em;
            padding: 2px 6px;
            border-radius: 10px;
            margin-left: 4px;
            font-weight: 600;
        }}

        .prs-section {{
            margin-top: 40px;
            padding-top: 30px;
            border-top: 2px solid #e0e0e0;
        }}

        .prs-section h2 {{
            color: #333;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}

        .fip-pr-group {{
            margin-bottom: 25px;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
        }}

        .fip-pr-header {{
            font-size: 1.2em;
            margin-bottom: 12px;
            color: #333;
        }}

        .pr-count {{
            color: #666;
            font-size: 0.9em;
            font-weight: normal;
        }}

        .pr-list {{
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}

        .pr-item {{
            background: white;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }}

        .pr-link {{
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
            display: block;
            margin-bottom: 4px;
        }}

        .pr-link:hover {{
            text-decoration: underline;
        }}

        .pr-meta {{
            color: #666;
            font-size: 0.85em;
        }}

        .no-prs {{
            text-align: center;
            padding: 40px;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Filecoin Improvement Proposals Dashboard</h1>
            <p>Real-time status tracking of all FIPs</p>
            <div class="last-updated">Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>

        <div class="controls">
            <div style="display: flex; gap: 10px;">
                <button class="refresh-btn" onclick="location.reload()">🔄 Refresh Page</button>
                <a href="fips-timeline-tracker.html" style="background: #28a745; color: white; padding: 12px 24px; border-radius: 6px; text-decoration: none; font-weight: 600; transition: all 0.3s; display: inline-block;">📅 View Timeline Tracker</a>
            </div>
            <div><span style="color: #28a745;">✅ Data loaded</span></div>
        </div>

        <div class="stats-summary">
            <div class="stat-card">
                <h3>Total FIPs</h3>
                <div class="number">{total_fips}</div>
            </div>
            <div class="stat-card">
                <h3>Final</h3>
                <div class="number">{final_count}</div>
            </div>
            <div class="stat-card">
                <h3>Draft</h3>
                <div class="number">{draft_count}</div>
            </div>
            <div class="stat-card">
                <h3>Active (Accepted/Last Call)</h3>
                <div class="number">{active_count}</div>
            </div>
        </div>

        <table class="status-table">
            <thead>
                <tr>
                    <th>Status</th>
                    <th>Count</th>
                    <th>FIPs</th>
                </tr>
            </thead>
            <tbody>
{''.join(table_rows)}
            </tbody>
        </table>

        {generate_prs_section_html(fip_prs)}
    </div>
</body>
</html>'''
    
    return html

def main():
    print("Fetching FIPs data from GitHub...")
    text = fetch_readme()
    
    if not text:
        print("Failed to fetch README")
        return
    
    print("Parsing FIPs...")
    fips = parse_fips(text)
    print(f"Found {len(fips)} FIPs")
    
    print("Fetching open PRs...")
    prs = fetch_open_prs()
    fip_prs = {}
    if prs:
        fip_prs = process_prs(prs)
        total_prs = sum(len(pr_list) for pr_list in fip_prs.values())
        print(f"Found {total_prs} PR(s) related to {len(fip_prs)} FIP(s)")
    
    print("Generating HTML dashboard...")
    html = generate_html(fips, fip_prs)
    
    output_file = 'fips-dashboard-static.html'
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"Dashboard generated successfully: {output_file}")
    print(f"Open {output_file} in your browser to view the dashboard")

if __name__ == '__main__':
    main()