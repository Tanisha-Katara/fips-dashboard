#!/usr/bin/env python3
"""Shared utilities for FIP parsing used by dashboard scripts."""

import re


def get_status_class(status):
    """Get CSS class for status badge."""
    status_lower = status.lower()
    if 'final' in status_lower:
        return 'status-final'
    elif 'draft' in status_lower:
        return 'status-draft'
    elif 'accepted' in status_lower:
        return 'status-accepted'
    elif 'deferred' in status_lower:
        return 'status-deferred'
    elif 'rejected' in status_lower:
        return 'status-rejected'
    elif 'withdrawn' in status_lower:
        return 'status-withdrawn'
    elif 'active' in status_lower:
        return 'status-active'
    elif 'last call' in status_lower:
        return 'status-last-call'
    elif 'superseded' in status_lower:
        return 'status-superseded'
    return 'status-draft'


def parse_fip_table(text):
    """Parse FIPs from README markdown table.

    Returns a list of dicts with keys: number, title, type, authors, status.
    FRCs are excluded (only rows where type == 'FIP' are returned).
    """
    fips = []
    lines = text.split('\n')

    in_table = False
    header_found = False

    for line in lines:
        if '| FIP #' in line and 'Status' in line:
            header_found = True
            in_table = True
            continue

        if header_found and re.match(r'^\|[\s\-|:]+$', line):
            continue

        if in_table and line.startswith('| ['):
            parts = [p.strip() for p in line.split('|') if p.strip()]

            if len(parts) >= 5:
                fip_match = re.search(r'\[(\d+)\]', parts[0])
                if fip_match:
                    number = fip_match.group(1)
                    title = parts[1] if len(parts) > 1 else ''
                    fip_type = parts[2] if len(parts) > 2 else 'FIP'
                    authors = parts[3] if len(parts) > 3 else ''
                    status = parts[4] if len(parts) > 4 else ''

                    if 'Superseded' in status:
                        status = 'Superseded'
                    else:
                        status = status.strip()

                    # Only include FIPs, exclude FRCs
                    if fip_type.strip().upper() == 'FIP':
                        fips.append({
                            'number': number.zfill(4),
                            'title': title,
                            'type': fip_type,
                            'authors': authors,
                            'status': status,
                        })

    return fips
