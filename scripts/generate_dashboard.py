#!/usr/bin/env python3
"""
============================================================
MyID Migration Dashboard Generator
============================================================
PURPOSE: Reads the Excel tracker and generates an HTML dashboard
         with charts, stats, and interactive modals.

HOW TO RUN:
    1. Open Terminal
    2. cd "/Users/sam.levine.-nd/Desktop/2026 Projects/MyID_Migration"
    3. python3 scripts/generate_dashboard.py

WHAT IT DOES:
    - Reads: Most recent .xlsx file in data/input/ folder
    - Creates: reports/MyID_Migration_Dashboard.html

TO UPDATE THE DASHBOARD:
    1. Download the Excel file from SharePoint
    2. Save it to data/input/ folder (add date suffix like _MMDDYY)
    3. Run this script
    4. Open the new HTML file in reports/

VERSIONING:
    - Major version (x.0): Increment manually for dashboard changes
    - Minor version (#.x): Auto-increments when data file changes

============================================================
"""

import csv
import os
import math
import json
import hashlib
from datetime import datetime
from pathlib import Path
from collections import defaultdict

# Try to import openpyxl for Excel support
try:
    from openpyxl import load_workbook
    EXCEL_SUPPORT = True
except ImportError:
    EXCEL_SUPPORT = False
    print("WARNING: openpyxl not installed. Install with: pip3 install openpyxl")
    print("Falling back to CSV mode.")

# ============================================================
# CONFIGURATION - Change these paths if needed
# ============================================================
SCRIPT_DIR = Path(__file__).parent
PROJECT_DIR = SCRIPT_DIR.parent

# Data input folder - script will find the most recent .xlsx file
DATA_INPUT_DIR = PROJECT_DIR / "data" / "input"
# Fallback: CSV in project folder
CSV_PATH = DATA_INPUT_DIR / "MyID_Migration_Tracker.csv"
OUTPUT_PATH = PROJECT_DIR / "reports" / "MyID_Migration_Dashboard.html"

# Version tracking
VERSION_FILE = PROJECT_DIR / "data" / "version_state.json"
CHANGELOG_PATH = PROJECT_DIR / "CHANGELOG.md"
DASHBOARD_MAJOR_VERSION = 2  # Increment this manually for major dashboard changes

# Legend for v3 format:
# ✓ = Yes, x = No, n/a = Not Applicable, ? = Unknown
# Obsolete = No migration required


# ============================================================
# VERSION MANAGEMENT
# ============================================================
def get_file_hash(filepath):
    """Calculate MD5 hash of a file to detect changes."""
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def load_version_state():
    """Load the current version state from JSON file."""
    if VERSION_FILE.exists():
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    return {
        'major': DASHBOARD_MAJOR_VERSION,
        'minor': 0,
        'last_data_hash': None,
        'last_data_file': None
    }


def save_version_state(state):
    """Save the version state to JSON file."""
    VERSION_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(VERSION_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def get_version_string(state):
    """Return version as string like 'v2.3'."""
    return f"v{state['major']}.{state['minor']}"


def update_version_if_needed(data_file_path, stats):
    """
    Check if data file changed and update version accordingly.
    Returns the current version string.
    """
    state = load_version_state()
    current_hash = get_file_hash(data_file_path)
    
    # Check if major version was manually updated in script
    if DASHBOARD_MAJOR_VERSION > state['major']:
        state['major'] = DASHBOARD_MAJOR_VERSION
        state['minor'] = 0
        state['last_data_hash'] = current_hash
        state['last_data_file'] = str(data_file_path.name)
        save_version_state(state)
        update_changelog(state, data_file_path.name, stats, is_major=True)
        return get_version_string(state)
    
    # Check if data file changed (different hash)
    if current_hash != state['last_data_hash']:
        state['minor'] += 1
        state['last_data_hash'] = current_hash
        state['last_data_file'] = str(data_file_path.name)
        save_version_state(state)
        update_changelog(state, data_file_path.name, stats, is_major=False)
    
    return get_version_string(state)


def update_changelog(state, data_filename, stats, is_major=False):
    """Append an entry to the CHANGELOG.md file."""
    today = datetime.now().strftime("%B %d, %Y")
    version = get_version_string(state)
    
    # Build the entry
    entry_lines = [f"\n## {version} - {today}\n"]
    
    if is_major:
        entry_lines.append("- **Dashboard Update:** Major version increment\n")
    
    entry_lines.append(f"- Data file: `{data_filename}`\n")
    entry_lines.append(f"- Stats: {stats['acme_done']} ACME Done, {stats['acme_to_do']} To Do, {stats['at_risk']} At Risk\n")
    
    # Read existing changelog or create header
    if CHANGELOG_PATH.exists():
        with open(CHANGELOG_PATH, 'r') as f:
            existing_content = f.read()
    else:
        existing_content = """# MyID Migration Dashboard Changelog

This file tracks all version changes to the dashboard.
- **Major versions (x.0):** Dashboard UI/logic changes
- **Minor versions (#.x):** Data file updates

---
"""
    
    # Insert new entry after the header (after the ---)
    header_end = existing_content.find('---')
    if header_end != -1:
        insert_pos = header_end + 4  # After "---\n"
        new_content = existing_content[:insert_pos] + ''.join(entry_lines) + existing_content[insert_pos:]
    else:
        new_content = existing_content + ''.join(entry_lines)
    
    with open(CHANGELOG_PATH, 'w') as f:
        f.write(new_content)


def find_latest_excel_file():
    """
    Find the most recently modified .xlsx file in the data/input directory.
    Returns the Path to the file, or None if no Excel files found.
    """
    excel_files = list(DATA_INPUT_DIR.glob("*.xlsx"))
    
    if not excel_files:
        return None
    
    # Sort by modification time, newest first
    excel_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    
    return excel_files[0]

# ============================================================
# STATUS NORMALIZATION
# Standardize status values to: Done, In Progress, To Do, Obsolete, N/A
# ============================================================
def normalize_status(status):
    """
    Normalize migration status values.
    Possible output values: Done, In Progress, To Do, Obsolete, N/A
    """
    if not status:
        return status
    status_lower = status.strip().lower()
    
    # Obsolete variants
    if status_lower in ['obsolete', 'not needed', 'no migration required', 'no migration needed', 'migration unneeded']:
        return 'Obsolete'
    
    # Done variants
    if status_lower in ['done', 'completed', 'complete']:
        return 'Done'
    
    # To Do variants (no more "Not Started")
    if status_lower in ['to do', 'todo', 'not started']:
        return 'To Do'
    
    # In Progress
    if status_lower in ['in progress', 'in-progress']:
        return 'In Progress'
    
    # N/A
    if status_lower in ['n/a', 'na', 'not applicable']:
        return 'N/A'
    
    return status.strip()

# ============================================================
# COLOR CONFIGURATION - Professional Business Palette
# ============================================================
COLORS = {
    'done': '#059669',           # Professional Green (emerald)
    'to_do': '#f59e0b',          # Warm Amber/Yellow
    'in_progress': '#3b82f6',    # Professional Blue
    'obsolete': '#64748b',       # Slate Gray
    'na': '#94a3b8',             # Light Slate Gray
    'at_risk': '#ea580c',        # Orange (warning)
    'primary': '#1e40af',        # Deep Blue
    'secondary': '#475569'       # Dark Slate
}

def read_excel_data(excel_path):
    """
    ============================================================
    SECTION: Excel Data Loading
    PURPOSE: Reads the Excel file and returns list of app records
    NOTE: Handles both old format and new SharePoint matrix format
    ============================================================
    """
    import warnings
    import zipfile
    import xml.etree.ElementTree as ET
    from datetime import datetime, timedelta
    warnings.filterwarnings('ignore', category=UserWarning)
    
    apps = []
    
    # Direct XML parsing (works for both standard and strict OOXML)
    print("  Using direct XML parser for strict OOXML format...")
    
    try:
        with zipfile.ZipFile(excel_path, 'r') as z:
            # Read shared strings (cell values are often stored here)
            shared_strings = []
            if 'xl/sharedStrings.xml' in z.namelist():
                ss_xml = z.read('xl/sharedStrings.xml').decode('utf-8')
                ss_xml = ss_xml.replace('http://purl.oclc.org/ooxml/spreadsheetml/main', 
                                       'http://schemas.openxmlformats.org/spreadsheetml/2006/main')
                root = ET.fromstring(ss_xml)
                for si in root.findall('.//{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                    shared_strings.append(si.text or '')
            
            # Read the worksheet
            sheet_xml = z.read('xl/worksheets/sheet1.xml').decode('utf-8')
            sheet_xml = sheet_xml.replace('http://purl.oclc.org/ooxml/spreadsheetml/main',
                                         'http://schemas.openxmlformats.org/spreadsheetml/2006/main')
            root = ET.fromstring(sheet_xml)
            
            ns = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
            
            # Parse all rows
            rows_data = []
            for row in root.findall(f'.//{{{ns}}}row'):
                row_values = {}
                for cell in row.findall(f'{{{ns}}}c'):
                    cell_ref = cell.get('r', '')
                    cell_type = cell.get('t', '')
                    col = ''.join(c for c in cell_ref if c.isalpha())
                    
                    value_elem = cell.find(f'{{{ns}}}v')
                    if value_elem is not None and value_elem.text:
                        if cell_type == 's':
                            idx = int(value_elem.text)
                            value = shared_strings[idx] if idx < len(shared_strings) else ''
                        else:
                            value = value_elem.text
                    else:
                        value = ''
                    
                    row_values[col] = value
                
                if row_values:
                    rows_data.append(row_values)
            
            if not rows_data:
                raise Exception("No data found in Excel file")
            
            # Detect format: Check if row 1 has 'System' in column B (new SharePoint format)
            is_new_format = len(rows_data) > 1 and rows_data[1].get('B', '').strip() == 'System'
            
            if is_new_format:
                print("  Detected v3 matrix format...")
                # V3 matrix format (MP&A_-_Okta-Based_MyID_Migration)
                # Row 0: Section headers (merged cells)
                # Row 1: Column headers
                # Row 2+: Data
                # Columns: A=Environment, B=System, C=POC, D=Obsolete, E=Sentry1.0, F=Sentry2.0, 
                #          G=Direct Int, H=Debut-Sentry, I=Auth Sys Status, J=SOLO, K=ACME, 
                #          L=Migration Status, M=Infra Access, N=Due Date, O=Future, P=JIRA, Q=Notes
                # Legend: ✓=Yes, x=No, n/a=N/A, ?=Unknown, Obsolete=No migration required
                
                # Helper functions for legend values
                # Legend: ✓=Yes, x=No, n/a=N/A, ?=Unknown
                def is_yes(val):
                    return val in ['✓', '✔', 'yes', 'Yes', 'YES', 'y', 'Y', 'true', 'True']
                
                def is_no(val):
                    return val in ['x', 'X', 'no', 'No', 'NO', 'n', 'N', 'false', 'False']
                
                def is_na(val):
                    return val.lower() in ['n/a', 'na', 'not applicable', ''] if val else True
                
                for row_values in rows_data[2:]:  # Skip header rows
                    app_name = row_values.get('A', '').strip()
                    if not app_name:
                        continue
                    
                    system = row_values.get('B', '').strip()
                    poc = row_values.get('C', '').strip()
                    obsolete = row_values.get('D', '').strip()       # ✓ = Obsolete (no migration)
                    sentry1 = row_values.get('E', '').strip()        # Sentry 1.0
                    sentry2 = row_values.get('F', '').strip()        # Sentry 2.0
                    direct_int = row_values.get('G', '').strip()     # Direct Integration
                    debut_sentry = row_values.get('H', '').strip()   # Debut-Sentry
                    auth_sys_status = row_values.get('I', '').strip() # Auth Sys Status (cross-check)
                    solo = row_values.get('J', '').strip()            # SOLO
                    acme = row_values.get('K', '').strip()            # ACME
                    migration_status = row_values.get('L', '').strip() # Migration Status (Done/In Progress/Obsolete/To Do)
                    infra_access = row_values.get('M', '').strip()    # Infra Access
                    due_date_raw = row_values.get('N', '').strip()    # Due Date
                    future = row_values.get('O', '').strip()          # Future
                    jira = row_values.get('P', '').strip()            # JIRA
                    # Notes column (Q) intentionally not used - does not drive dashboard data
                    
                    # Convert Excel date serial to readable date
                    due_date = ''
                    if due_date_raw:
                        try:
                            serial = int(float(due_date_raw))
                            date_obj = datetime(1899, 12, 30) + timedelta(days=serial)
                            due_date = date_obj.strftime('%m/%d/%Y')
                        except:
                            due_date = due_date_raw
                    
                    # =========================================================
                    # OBSOLETE CHECK (Column D)
                    # If Obsolete = ✓, OR Column L = "Obsolete", entire row is Obsolete
                    # =========================================================
                    migration_status_lower = migration_status.lower() if migration_status else ''
                    
                    if is_yes(obsolete) or migration_status_lower == 'obsolete':
                        acme_status = 'Obsolete'
                        sentry_status = 'Obsolete'
                    else:
                        # =========================================================
                        # ACME Migration Status (SOLO → ACME track)
                        # Column L is primary: Done, In Progress, To Do
                        # Columns J/K are secondary cross-check
                        # =========================================================
                        if migration_status_lower == 'done':
                            acme_status = 'Done'
                        elif is_yes(acme):
                            acme_status = 'Done'  # K = ✓ means on ACME = off SOLO
                        elif migration_status_lower == 'in progress':
                            acme_status = 'In Progress'
                        elif migration_status_lower in ['to do', 'todo']:
                            acme_status = 'To Do'
                        elif is_yes(solo) and not is_yes(acme):
                            acme_status = 'To Do'  # Still on SOLO, needs migration
                        else:
                            acme_status = 'To Do'
                        
                        # =========================================================
                        # Sentry Migration Status (Sentry 1.0 → Sentry 2.0/Direct Int/Debut-Sentry)
                        # Off Sentry 1.0 = ✓ in F (Sentry 2.0) OR G (Direct Int) OR H (Debut-Sentry)
                        # Column I (Auth Sys Status) is cross-check
                        # Only ONE of E/F/G/H will have ✓
                        # =========================================================
                        if is_yes(sentry2) or is_yes(direct_int) or is_yes(debut_sentry):
                            # Off Sentry 1.0 - on one of the target auth systems
                            sentry_status = 'Done'
                        elif is_yes(sentry1):
                            # Still on Sentry 1.0 - check Column I for status
                            auth_status_lower = auth_sys_status.lower() if auth_sys_status else ''
                            if auth_status_lower == 'done':
                                sentry_status = 'Done'  # Auth sys says done
                            elif auth_status_lower == 'in progress':
                                sentry_status = 'In Progress'
                            elif auth_status_lower in ['to do', 'todo']:
                                sentry_status = 'To Do'
                            else:
                                sentry_status = 'To Do'  # Default: still on Sentry 1.0
                        elif is_na(sentry1) and is_na(sentry2) and is_na(direct_int) and is_na(debut_sentry):
                            sentry_status = 'N/A'  # Not using any auth system (SOLO-only)
                        elif is_no(sentry1) and is_no(sentry2) and is_no(direct_int) and is_no(debut_sentry):
                            sentry_status = 'N/A'  # Not using any Sentry
                        else:
                            sentry_status = 'N/A'
                    
                    # Extract environment from app name
                    env = ''
                    if '-int' in app_name.lower():
                        env = 'INT'
                    elif '-prd' in app_name.lower() or '-prod' in app_name.lower():
                        env = 'PRD'
                    elif '-stg' in app_name.lower() or '-stage' in app_name.lower():
                        env = 'STG'
                    elif '-qat' in app_name.lower():
                        env = 'QAT'
                    
                    # Determine current auth system for display
                    if is_yes(sentry2):
                        current_auth = 'Sentry 2.0'
                    elif is_yes(direct_int):
                        current_auth = 'Direct Integration'
                    elif is_yes(debut_sentry):
                        current_auth = 'Debut-Sentry'
                    elif is_yes(sentry1):
                        current_auth = 'Sentry 1.0'
                    else:
                        current_auth = 'N/A'
                    
                    # Determine if at risk (due date is 2/27/26 and not done)
                    at_risk = 'No'
                    if due_date and '02/27/2026' in due_date and acme_status != 'Done':
                        at_risk = 'Yes'
                    
                    apps.append({
                        'Platform/App': app_name,
                        'Environment': env,
                        'System': system,
                        'Owner': poc,
                        'Tech Lead': poc,
                        'ACME Migration Status': acme_status,
                        'ACME Target Deadline': due_date,
                        'Sentry Migration Status': sentry_status,
                        'Auth System': current_auth,
                        'Auth Sys Status': auth_sys_status,
                        'Migration Status Raw': migration_status,
                        'JIRA Ticket': jira,
                        'At Risk for 2/27/26': at_risk,
                        'Blocker': ''
                    })
            else:
                print("  Using original format...")
                # Original format: Row 0 is headers
                header_row = rows_data[0]
                cols = sorted(header_row.keys(), key=lambda x: (len(x), x))
                headers = [header_row.get(c, '') for c in cols]
                
                for row_values in rows_data[1:]:
                    row_data = {}
                    for i, col in enumerate(cols):
                        if i < len(headers):
                            row_data[headers[i]] = row_values.get(col, '')
                    
                    if row_data.get('Platform/App', ''):
                        apps.append(row_data)
            
    except Exception as e:
        raise Exception(f"Failed to parse Excel file: {e}")
    
    if not apps:
        raise Exception("No valid data rows found in Excel file")
    
    return apps

def find_csv_file():
    """
    Find a CSV file in data/input/ for fallback when no Excel is present.
    Prefers Demo_*.csv for showcase repos, then any .csv.
    """
    csv_files = list(DATA_INPUT_DIR.glob("*.csv"))
    if not csv_files:
        return None
    # Prefer demo CSV if present (for portfolio/showcase repos)
    demo = [f for f in csv_files if f.name.startswith("Demo_")]
    if demo:
        demo.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        return demo[0]
    csv_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
    return csv_files[0]


def read_csv_data(csv_path=None):
    """
    ============================================================
    SECTION: CSV Data Loading (Fallback)
    PURPOSE: Reads the CSV file and returns list of app records
    CSV columns: Platform/App, System, ACME Migration Status, etc.
    Auth System is set from "Current Auth System" if present (for quadrant).
    ============================================================
    """
    path = csv_path or CSV_PATH
    apps = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if not row.get('Platform/App', '').strip():
                continue
            # Map Current Auth System → Auth System for quadrant logic
            if 'Auth System' not in row and row.get('Current Auth System'):
                row['Auth System'] = row['Current Auth System']
            elif 'Auth System' not in row:
                row['Auth System'] = ''
            apps.append(row)
    return apps


def read_data():
    """
    ============================================================
    SECTION: Data Loading
    PURPOSE: Reads from Excel (primary) or CSV (fallback)
    Auto-detects the most recent .xlsx file in data/input/
    ============================================================
    """
    excel_file = find_latest_excel_file()
    
    if EXCEL_SUPPORT and excel_file:
        print(f"Reading from Excel: {excel_file.name}")
        return read_excel_data(excel_file), "Excel", excel_file
    
    csv_file = find_csv_file()
    if csv_file:
        print(f"Reading from CSV: {csv_file.name}")
        return read_csv_data(csv_file), "CSV", csv_file
    
    raise FileNotFoundError(f"No data file found in {DATA_INPUT_DIR}. Add an .xlsx or .csv file.")

def filter_deactivated_apps(apps):
    """
    ============================================================
    SECTION: Deactivated Apps Filter
    PURPOSE: Separates apps marked as "(Not in use)" from active apps
    Checks: System, Platform/App, and status columns (Notes intentionally excluded)
    ============================================================
    """
    active_apps = []
    deactivated_apps = []
    
    for app in apps:
        # Check relevant fields for "(Not in use)" indicator - Notes excluded
        system = app.get('System', '')
        app_name = app.get('Platform/App', '')
        acme_status = app.get('ACME Migration Status', '')
        sentry_status = app.get('Sentry Migration Status', '')
        
        # Combine fields and check for "not in use" - Notes intentionally not included
        all_text = f"{system} {app_name} {acme_status} {sentry_status}".lower()
        
        if '(not in use)' in all_text or 'not in use' in all_text:
            deactivated_apps.append(app)
        else:
            active_apps.append(app)
    
    return active_apps, deactivated_apps

def calculate_stats(apps):
    """
    ============================================================
    SECTION: Statistics Calculation
    PURPOSE: Counts apps by status for dashboard cards
    NOTE: Obsolete apps are excluded before this is called.
          Stats only count non-obsolete active apps.
    ============================================================
    """
    stats = {
        'acme_done': 0,
        'acme_to_do': 0,
        'acme_in_progress': 0,
        'sentry_done': 0,
        'sentry_to_do': 0,
        'sentry_in_progress': 0,
        'sentry_na': 0,
        'at_risk': 0,
        'total': len(apps)
    }
    
    for app in apps:
        acme_status = normalize_status(app.get('ACME Migration Status', ''))
        sentry_status = normalize_status(app.get('Sentry Migration Status', ''))
        at_risk = app.get('At Risk for 2/27/26', '').strip().lower()
        
        # ACME stats (SOLO → ACME track)
        if acme_status == 'Done':
            stats['acme_done'] += 1
        elif acme_status == 'In Progress':
            stats['acme_in_progress'] += 1
        elif acme_status == 'To Do':
            stats['acme_to_do'] += 1
        
        # Sentry stats (Sentry 1.0 → Sentry 2.0/Direct Int/Debut-Sentry track)
        if sentry_status == 'Done':
            stats['sentry_done'] += 1
        elif sentry_status == 'In Progress':
            stats['sentry_in_progress'] += 1
        elif sentry_status == 'To Do':
            stats['sentry_to_do'] += 1
        elif sentry_status == 'N/A':
            stats['sentry_na'] += 1
        
        # At risk
        if at_risk == 'yes':
            stats['at_risk'] += 1
    
    return stats

def group_apps_by_status(apps):
    """
    ============================================================
    SECTION: App Grouping
    PURPOSE: Groups apps by their status for modal popups
    NOTE: Obsolete apps excluded before this is called.
    ============================================================
    """
    groups = {
        'acme_done': [],
        'acme_to_do': [],
        'acme_in_progress': [],
        'sentry_done': [],
        'sentry_to_do': [],
        'sentry_in_progress': [],
        'sentry_na': [],
        'at_risk': [],
        'future': []
    }
    
    for app in apps:
        acme_status = normalize_status(app.get('ACME Migration Status', ''))
        sentry_status = normalize_status(app.get('Sentry Migration Status', ''))
        at_risk = app.get('At Risk for 2/27/26', '').strip().lower()
        deadline = app.get('ACME Target Deadline', '').strip()
        
        # ACME grouping (SOLO → ACME track)
        if acme_status == 'Done':
            groups['acme_done'].append(app)
        elif acme_status == 'In Progress':
            groups['acme_in_progress'].append(app)
        elif acme_status == 'To Do':
            groups['acme_to_do'].append(app)
        
        # Sentry grouping (Sentry 1.0 → 2.0/Direct Int/Debut-Sentry track)
        if sentry_status == 'Done':
            groups['sentry_done'].append(app)
        elif sentry_status == 'In Progress':
            groups['sentry_in_progress'].append(app)
        elif sentry_status == 'To Do':
            groups['sentry_to_do'].append(app)
        elif sentry_status == 'N/A':
            groups['sentry_na'].append(app)
        
        # At risk
        if at_risk == 'yes':
            groups['at_risk'].append(app)
        
        # Future (no deadline)
        if deadline == 'Future' and acme_status == 'To Do':
            groups['future'].append(app)
    
    return groups

def calculate_tech_lead_workload(apps):
    """
    ============================================================
    SECTION: Tech Lead Workload
    PURPOSE: Calculates work distribution by tech lead
    ============================================================
    """
    workload = defaultdict(lambda: {'done': 0, 'to_do': 0, 'in_progress': 0})
    
    for app in apps:
        lead = app.get('Tech Lead', '').strip()
        if not lead:
            continue
        
        acme_status = normalize_status(app.get('ACME Migration Status', ''))
        
        if acme_status == 'Done':
            workload[lead]['done'] += 1
        elif acme_status == 'To Do':
            workload[lead]['to_do'] += 1
        elif acme_status == 'In Progress':
            workload[lead]['in_progress'] += 1
    
    return dict(workload)

def calculate_system_migration_matrix(apps):
    """
    ============================================================
    SECTION: System Migration Matrix
    PURPOSE: Categorizes apps by system for two independent tracks:
             1. SOLO → ACME (OFF SOLO)
             2. Sentry 1.0 → Sentry 2.0/Direct Int/Debut-Sentry (OFF SENTRY 1)
    NOTE: Obsolete apps are excluded before this function is called.
    ============================================================
    """
    systems = defaultdict(lambda: {
        # SOLO → ACME track (store full app dicts for modal details)
        'on_acme': [],         # Off SOLO (ACME = ✓ or status = Done)
        'not_on_acme': [],     # Still on SOLO (needs migration)
        # Sentry track (only for apps that use Sentry)
        'off_sentry1': [],     # Off Sentry 1.0 (on Sentry 2.0/Direct Int/Debut-Sentry)
        'on_sentry1': [],      # Still on Sentry 1.0
        'no_sentry': [],       # N/A - not using any Sentry
        # Track target auth system for completed apps (for quadrant positioning)
        'on_debut_sentry': [], # Apps that migrated TO Debut-Sentry
        'on_sentry2': [],      # Apps that migrated TO Sentry 2.0 or Direct Integration
    })
    
    for app in apps:
        system = app.get('System', 'Unknown').strip() or 'Unknown'
        acme_status = normalize_status(app.get('ACME Migration Status', ''))
        sentry_status = normalize_status(app.get('Sentry Migration Status', ''))
        auth_system = app.get('Auth System', '')
        
        # SOLO → ACME track: Is this app OFF SOLO?
        if acme_status == 'Done':
            systems[system]['on_acme'].append(app)
        else:
            systems[system]['not_on_acme'].append(app)
        
        # Sentry track: Is this app OFF Sentry 1.0?
        if sentry_status == 'Done':
            systems[system]['off_sentry1'].append(app)
            # Track which auth system they migrated TO
            if auth_system == 'Debut-Sentry':
                systems[system]['on_debut_sentry'].append(app)
            else:
                systems[system]['on_sentry2'].append(app)  # Sentry 2.0 or Direct Integration
        elif sentry_status in ['To Do', 'In Progress']:
            systems[system]['on_sentry1'].append(app)
        else:
            systems[system]['no_sentry'].append(app)  # N/A
    
    # Calculate summary stats for each system
    result = {}
    for system, grps in systems.items():
        total = len(grps['on_acme']) + len(grps['not_on_acme'])
        
        # Off SOLO = on ACME
        off_solo = len(grps['on_acme'])
        
        # Off Sentry 1.0 (only counting apps that use Sentry)
        sentry_apps = len(grps['off_sentry1']) + len(grps['on_sentry1'])
        off_sentry1 = len(grps['off_sentry1'])
        
        # Determine target auth system for this system (for quadrant positioning)
        # If any apps migrated to Debut-Sentry and none to Sentry 2.0, target is Debut-Sentry
        on_debut = len(grps['on_debut_sentry'])
        on_s2 = len(grps['on_sentry2'])
        if on_debut > 0 and on_s2 == 0:
            target_auth = 'Debut-Sentry'
        elif on_s2 > 0:
            target_auth = 'Sentry 2.0'
        else:
            target_auth = 'Sentry 2.0'  # Default target
        
        result[system] = {
            'groups': grps,
            'total': total,
            'off_solo': off_solo,
            'off_solo_pct': int((off_solo / total * 100)) if total > 0 else 0,
            'sentry_total': sentry_apps,
            'off_sentry1': off_sentry1,
            'off_sentry1_pct': int((off_sentry1 / sentry_apps * 100)) if sentry_apps > 0 else -1,  # -1 = N/A
            'target_auth': target_auth,  # Where the system is migrating TO
        }
    
    return result

def generate_modal_data_js(groups):
    """
    ============================================================
    SECTION: Modal Data Generation
    PURPOSE: Creates JavaScript object for popup modals
    ============================================================
    """
    def app_to_js(app, extra_fields=None):
        """Convert app dict to JS object string"""
        js_obj = {
            'name': app.get('Platform/App', ''),
            'env': app.get('Environment', ''),
            'system': app.get('System', ''),
        }
        if app.get('Tech Lead'):
            js_obj['lead'] = app.get('Tech Lead')
        if app.get('Owner'):
            js_obj['owner'] = app.get('Owner')
        if app.get('ACME Target Deadline'):
            js_obj['deadline'] = app.get('ACME Target Deadline')
        if app.get('Blocker'):
            js_obj['blocker'] = app.get('Blocker')
        if app.get('JIRA Ticket'):
            js_obj['jira'] = app.get('JIRA Ticket')
        # Notes intentionally excluded from modal display
        if extra_fields:
            js_obj.update(extra_fields)
        
        pairs = []
        for k, v in js_obj.items():
            # Escape special characters that break JavaScript strings
            v_escaped = str(v).replace("\\", "\\\\").replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n').replace('\r', '')
            pairs.append(f"{k}: '{v_escaped}'")
        return '{ ' + ', '.join(pairs) + ' }'
    
    modal_data = []
    
    # ACME Done
    apps_js = ',\n                    '.join([app_to_js(a) for a in groups['acme_done']])
    modal_data.append(f"""
            'acme-done': {{
                title: 'ACME Done (Off SOLO)',
                titleColor: '{COLORS["done"]}',
                count: {len(groups['acme_done'])},
                description: 'These applications have successfully completed their SOLO → ACME migration.',
                color: 'green',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # ACME In Progress
    apps_js = ',\n                    '.join([app_to_js(a) for a in groups['acme_in_progress']])
    modal_data.append(f"""
            'acme-in-progress': {{
                title: 'ACME In Progress',
                titleColor: '{COLORS["in_progress"]}',
                count: {len(groups['acme_in_progress'])},
                description: 'These applications are currently migrating from SOLO to ACME.',
                color: 'blue',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # ACME To Do
    apps_js = ',\n                    '.join([app_to_js(a) for a in groups['acme_to_do']])
    modal_data.append(f"""
            'acme-to-do': {{
                title: 'ACME To Do',
                titleColor: '{COLORS["to_do"]}',
                count: {len(groups['acme_to_do'])},
                description: 'These applications still need to begin their SOLO → ACME migration.',
                color: 'amber',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # Sentry Done
    apps_js = ',\n                    '.join([app_to_js(a, {'auth': a.get('Auth System', '')}) for a in groups['sentry_done']])
    modal_data.append(f"""
            'sentry-done': {{
                title: 'Off Sentry 1.0 (Done)',
                titleColor: '{COLORS["done"]}',
                count: {len(groups['sentry_done'])},
                description: 'These applications have migrated off Sentry 1.0 to Sentry 2.0, Direct Integration, or Debut-Sentry.',
                color: 'green',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # Sentry In Progress
    apps_js = ',\n                    '.join([app_to_js(a) for a in groups['sentry_in_progress']])
    modal_data.append(f"""
            'sentry-in-progress': {{
                title: 'Sentry Migration In Progress',
                titleColor: '{COLORS["in_progress"]}',
                count: {len(groups['sentry_in_progress'])},
                description: 'These applications are currently migrating off Sentry 1.0.',
                color: 'blue',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # Sentry To Do
    apps_js = ',\n                    '.join([app_to_js(a) for a in groups['sentry_to_do']])
    modal_data.append(f"""
            'sentry-to-do': {{
                title: 'Sentry To Do (Still on Sentry 1.0)',
                titleColor: '{COLORS["to_do"]}',
                count: {len(groups['sentry_to_do'])},
                description: 'These applications are currently on Sentry 1.0 and need to migrate.',
                color: 'amber',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # Sentry N/A
    apps_js = ',\n                    '.join([app_to_js(a) for a in groups['sentry_na']])
    modal_data.append(f"""
            'sentry-na': {{
                title: 'N/A - SOLO Apps (Not Using Sentry)',
                titleColor: '{COLORS["na"]}',
                count: {len(groups['sentry_na'])},
                description: 'These apps do not use Sentry. Sentry migration does not apply.',
                color: 'gray',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    # At Risk
    at_risk_apps = []
    for a in groups['at_risk']:
        extra = {
            'acme': a.get('ACME Migration Status', ''),
            'sentry': a.get('Sentry Migration Status', '')
        }
        at_risk_apps.append(app_to_js(a, extra))
    apps_js = ',\n                    '.join(at_risk_apps)
    modal_data.append(f"""
            'at-risk': {{
                title: 'At Risk for 2/27/26 Deadline',
                titleColor: '{COLORS["at_risk"]}',
                count: {len(groups['at_risk'])},
                description: 'These applications need migration work completed before February 27, 2026.',
                color: 'orange',
                apps: [
                    {apps_js}
                ]
            }}""")
    
    return ','.join(modal_data)

def generate_html(stats, groups, workload, system_matrix, active_apps_for_overview, obsolete_apps, deactivated_apps, data_source, version="v2.0"):
    """
    ============================================================
    SECTION: HTML Generation
    PURPOSE: Creates the complete HTML dashboard file
    ============================================================
    """
    today = datetime.now().strftime("%B %d, %Y")
    
    # Calculate ACME progress percentage (SOLO → ACME track)
    acme_requiring_migration = stats['acme_done'] + stats['acme_to_do'] + stats['acme_in_progress']
    if acme_requiring_migration > 0:
        progress_pct = int((stats['acme_done'] / acme_requiring_migration) * 100)
    else:
        progress_pct = 0
    
    # Calculate Sentry progress percentage (Sentry 1.0 → off Sentry 1.0)
    sentry_requiring_migration = stats['sentry_done'] + stats['sentry_to_do'] + stats['sentry_in_progress']
    if sentry_requiring_migration > 0:
        sentry_progress_pct = int((stats['sentry_done'] / sentry_requiring_migration) * 100)
    else:
        sentry_progress_pct = 0
    
    # Tech lead labels and data for chart
    tech_leads = list(workload.keys())
    done_data = [workload[t]['done'] for t in tech_leads]
    to_do_data = [workload[t]['to_do'] for t in tech_leads]
    in_progress_data = [workload[t]['in_progress'] for t in tech_leads]
    
    # System migration matrix data
    system_names = sorted(system_matrix.keys())
    
    # Quadrant bubble chart data
    # Position bubbles INSIDE their correct quadrant cell (not at edges/corners)
    # The chart is 2 columns (SOLO | ACME) x 3 rows (Sentry 1.0 | Debut-Sentry | Sentry 2.0)
    # 
    # Quadrant cell centers:
    #   X: SOLO side = 25, ACME side = 75
    #   Y: Sentry 1.0 row = 83, Debut row = 50, Sentry 2.0 row = 17
    #
    # A system goes in the quadrant cell that represents its current state.
    # Being IN the cell = that's where the system IS, not where it's going.
    
    quadrant_bubbles = []
    
    # Track how many systems land in each cell for spread
    cell_counts = defaultdict(list)
    
    for system in system_names:
        data = system_matrix[system]
        is_na_sentry = data['off_sentry1_pct'] == -1
        
        # Determine which column: SOLO (left) or ACME (right)
        # Partial progress (0 < pct < 100) → ACME side (in progress toward ACME)
        if data['off_solo_pct'] >= 100:
            x_side = 'acme'
        elif data['off_solo_pct'] > 0:
            x_side = 'partial_acme'
        else:
            x_side = 'solo'
        
        # Determine which row: Sentry 1.0 (top), Debut Sentry (middle), Sentry 2.0/Done (bottom)
        # A system should be in the Sentry 1.0 row if ANY of its apps are still on Sentry 1.0
        # When 100% off Sentry 1.0, position depends on TARGET auth system:
        #   - Debut-Sentry target → middle row
        #   - Sentry 2.0/Direct Integration target → bottom row
        if is_na_sentry:
            y_row = 'na'  # No Sentry involvement
        elif data['off_sentry1_pct'] >= 100:
            # Fully off Sentry 1.0 - position based on target auth system
            if data.get('target_auth') == 'Debut-Sentry':
                y_row = 'debut'  # Migrated to Debut-Sentry
            else:
                y_row = 's2'  # Migrated to Sentry 2.0 or Direct Integration
        elif data['off_sentry1_pct'] < 100:
            # Still has apps on Sentry 1.0 - stays in top row until migration complete
            y_row = 's1'
        else:
            y_row = 's1'  # Default: Still on Sentry 1.0
        
        cell_key = f"{x_side}_{y_row}"
        cell_counts[cell_key].append(system)
        
        # Color based on progress
        if data['off_solo_pct'] >= 100 and (is_na_sentry or data['off_sentry1_pct'] >= 100):
            color = '#059669'  # Green - fully done
        elif data['off_solo_pct'] >= 100 or (not is_na_sentry and data['off_sentry1_pct'] >= 100):
            color = '#22c55e'  # Light green - one track done
        elif data['off_solo_pct'] > 0 or (not is_na_sentry and data['off_sentry1_pct'] > 0):
            color = '#f59e0b'  # Amber - in progress
        else:
            color = '#dc2626'  # Red - not started
        
        # Build display strings
        if is_na_sentry:
            sentry_display = "N/A (SOLO)"
        else:
            sentry_display = f"{data['off_sentry1']}/{data['sentry_total']} off Sentry 1.0"
        
        acme_display = f"{data['off_solo']}/{data['total']} off SOLO ({data['off_solo_pct']}%)"
        
        quadrant_bubbles.append({
            'system': system,
            'cell_key': cell_key,
            'r': 18,
            'label': system,
            'total': data['total'],
            'color': color,
            'solo_only': is_na_sentry,
            'acme_display': acme_display,
            'sentry_display': sentry_display,
            'off_solo_pct': data['off_solo_pct'],
            'off_sentry1_pct': data['off_sentry1_pct']
        })
    
    # Now assign x,y positions based on cell placement with spread
    # Cell center positions
    cell_centers = {
        # X positions: solo=25, partial_acme=65, acme=75
        # Y positions: s1=83, debut=50, s2=17, na=50
    }
    
    for bubble in quadrant_bubbles:
        ck = bubble['cell_key']
        parts = ck.split('_', 1)
        x_side = parts[0]
        y_row = parts[1] if len(parts) > 1 else 'na'
        
        # Base center positions (well inside each cell)
        if x_side == 'solo':
            cx = 25
        elif x_side == 'partial_acme':
            cx = 65
        else:
            cx = 75
        
        if y_row == 's1':
            cy = 83
        elif y_row == 'debut':
            cy = 50
        elif y_row == 's2':
            cy = 17
        else:  # na
            cy = 50
        
        # Spread multiple bubbles in same cell
        siblings = cell_counts[ck]
        idx = siblings.index(bubble['system'])
        count = len(siblings)
        
        if count == 1:
            x_pos, y_pos = cx, cy
        elif count == 2:
            offsets = [(-10, 0), (10, 0)]
            x_pos = cx + offsets[idx][0]
            y_pos = cy + offsets[idx][1]
        elif count == 3:
            offsets = [(-12, -5), (12, -5), (0, 8)]
            x_pos = cx + offsets[idx][0]
            y_pos = cy + offsets[idx][1]
        else:
            # Grid layout for 4+
            cols = 2
            row_i = idx // cols
            col_i = idx % cols
            x_pos = cx + (col_i - 0.5) * 18
            y_pos = cy + (row_i - 0.5) * 14
        
        # Clamp to stay well inside chart area (leave room for bubble radius)
        if x_side == 'solo' or x_side == 'partial_acme' and x_pos < 50:
            x_pos = max(10, min(45, x_pos))
        else:
            x_pos = max(55, min(90, x_pos))
        
        if y_row == 's1':
            y_pos = max(70, min(95, y_pos))
        elif y_row in ['debut', 'na']:
            y_pos = max(38, min(62, y_pos))
        else:  # s2
            y_pos = max(5, min(30, y_pos))
        
        bubble['x'] = x_pos
        bubble['y'] = y_pos
        
        # Remove temp keys before JSON (keep off_solo_pct, off_sentry1_pct for tooltip)
        del bubble['system']
        del bubble['cell_key']
    
    # Convert to JavaScript-compatible format
    quadrant_bubbles_js = json.dumps(quadrant_bubbles)
    
    # Build system summary for the table (badges are clickable)
    system_summary_rows = []
    for system in system_names:
        data = system_matrix[system]
        sys_key = system.lower().replace(' ', '-')
        
        # Off SOLO status - clickable
        if data['off_solo'] == data['total']:
            solo_status = f'<span class="status-badge done clickable-badge" onclick="showSystemModal(\'sys-solo-{sys_key}\')">100% Done</span>'
        elif data['off_solo'] == 0:
            solo_status = f'<span class="status-badge to-do clickable-badge" onclick="showSystemModal(\'sys-solo-{sys_key}\')">0/{data["total"]}</span>'
        else:
            solo_status = f'<span class="status-badge in-progress clickable-badge" onclick="showSystemModal(\'sys-solo-{sys_key}\')">{data["off_solo"]}/{data["total"]} ({data["off_solo_pct"]}%)</span>'
        
        # Off Sentry 1.0 status - clickable
        if data['off_sentry1_pct'] == -1:
            sentry_status = '<span style="color: #94a3b8;">N/A (SOLO)</span>'
        elif data['off_sentry1'] == data['sentry_total']:
            sentry_status = f'<span class="status-badge done clickable-badge" onclick="showSystemModal(\'sys-sentry-{sys_key}\')">100% Done</span>'
        elif data['off_sentry1'] == 0:
            sentry_status = f'<span class="status-badge to-do clickable-badge" onclick="showSystemModal(\'sys-sentry-{sys_key}\')">0/{data["sentry_total"]}</span>'
        else:
            sentry_status = f'<span class="status-badge in-progress clickable-badge" onclick="showSystemModal(\'sys-sentry-{sys_key}\')">{data["off_sentry1"]}/{data["sentry_total"]} ({data["off_sentry1_pct"]}%)</span>'
        
        system_summary_rows.append(f'''
                <tr>
                    <td><strong>{system}</strong></td>
                    <td style="text-align: center;">{data["total"]}</td>
                    <td style="text-align: center;">{solo_status}</td>
                    <td style="text-align: center;">{sentry_status}</td>
                </tr>''')
    system_summary_table = '\n'.join(system_summary_rows)
    
    # Generate per-system modal data for clickable badges
    system_modal_entries = []
    for system in system_names:
        data = system_matrix[system]
        grps = data['groups']
        
        # Helper to build app list JS for system modals
        def sys_app_js(app_list):
            items = []
            for a in app_list:
                name = str(a.get('Platform/App', '')).replace("'", "\\'")
                env = str(a.get('Environment', '')).replace("'", "\\'")
                status = str(a.get('ACME Migration Status', '')).replace("'", "\\'")
                sentry = str(a.get('Sentry Migration Status', '')).replace("'", "\\'")
                auth = str(a.get('Auth System', '')).replace("'", "\\'")
                jira = str(a.get('JIRA Ticket', '')).replace("'", "\\'")
                items.append(f"{{ name: '{name}', env: '{env}', acmeStatus: '{status}', sentryStatus: '{sentry}', auth: '{auth}', jira: '{jira}' }}")
            return ',\n                    '.join(items)
        
        safe_sys = system.replace("'", "\\'")
        
        # OFF SOLO modal - show remaining (not_on_acme) apps
        remaining_solo = sys_app_js(grps['not_on_acme'])
        done_solo = sys_app_js(grps['on_acme'])
        system_modal_entries.append(f"""
            'sys-solo-{system.lower().replace(' ', '-')}': {{
                title: '{safe_sys} — SOLO → ACME',
                titleColor: '{COLORS["primary"]}',
                systemSummary: '{data["off_solo"]}/{data["total"]} off SOLO ({data["off_solo_pct"]}%)',
                done: [
                    {done_solo}
                ],
                remaining: [
                    {remaining_solo}
                ]
            }}""")
        
        # OFF SENTRY modal - show remaining (on_sentry1) apps
        remaining_sentry = sys_app_js(grps['on_sentry1'])
        done_sentry = sys_app_js(grps['off_sentry1'])
        system_modal_entries.append(f"""
            'sys-sentry-{system.lower().replace(' ', '-')}': {{
                title: '{safe_sys} — Off Sentry 1.0',
                titleColor: '{COLORS["secondary"]}',
                systemSummary: '{data["off_sentry1"]}/{data["sentry_total"]} off Sentry 1.0',
                done: [
                    {done_sentry}
                ],
                remaining: [
                    {remaining_sentry}
                ]
            }}""")
    
    system_modal_js = ','.join(system_modal_entries)
    
    # Generate overview modal data (for the Overview & Risk card numbers)
    # Active Apps modal: list all active apps grouped by status
    active_apps_js_items = []
    for a in active_apps_for_overview:
        name = str(a.get('Platform/App', '')).replace("'", "\\'")
        env = str(a.get('Environment', '')).replace("'", "\\'")
        system_name = str(a.get('System', '')).replace("'", "\\'")
        acme_st = str(a.get('ACME Migration Status', '')).replace("'", "\\'")
        sentry_st = str(a.get('Sentry Migration Status', '')).replace("'", "\\'")
        active_apps_js_items.append(f"{{ name: '{name}', env: '{env}', system: '{system_name}', acme: '{acme_st}', sentry: '{sentry_st}' }}")
    active_apps_js = ',\n                    '.join(active_apps_js_items)
    
    obsolete_apps_js_items = []
    for a in obsolete_apps:
        name = str(a.get('Platform/App', '')).replace("'", "\\'")
        system_name = str(a.get('System', '')).replace("'", "\\'")
        owner = str(a.get('Owner', '')).replace("'", "\\'")
        obsolete_apps_js_items.append(f"{{ name: '{name}', system: '{system_name}', owner: '{owner}' }}")
    obsolete_apps_js = ',\n                    '.join(obsolete_apps_js_items)
    
    modal_data_js = generate_modal_data_js(groups)
    
    # Generate at-risk table rows
    at_risk_rows = []
    for app in groups['at_risk']:
        acme_status = app.get('ACME Migration Status', '')
        sentry_status = app.get('Sentry Migration Status', '')
        jira = app.get('JIRA Ticket', '-')
        status_class = 'to-do' if acme_status == 'To Do' else 'in-progress'
        at_risk_rows.append(f"""
                <tr>
                    <td>{app.get('Platform/App', '')}</td>
                    <td>{app.get('Environment', '')}</td>
                    <td>{app.get('System', '')}</td>
                    <td>{app.get('Tech Lead', '')}</td>
                    <td><span class="status-badge {status_class}">{acme_status}</span></td>
                    <td>{sentry_status}</td>
                    <td>{jira}</td>
                </tr>""")
    at_risk_table = '\n'.join(at_risk_rows)
    
    # Generate future work table rows
    future_rows = []
    for app in groups['future']:
        future_rows.append(f"""
                <tr>
                    <td>{app.get('Platform/App', '')}</td>
                    <td>{app.get('Environment', '')}</td>
                    <td>{app.get('System', '')}</td>
                    <td>{app.get('Tech Lead', '')}</td>
                    <td><span class="status-badge to-do">To Do</span></td>
                    <td>{app.get('JIRA Ticket', '-')}</td>
                </tr>""")
    future_table = '\n'.join(future_rows)
    
    # Generate obsolete apps table rows
    obsolete_rows = []
    for app in obsolete_apps:
        system = app.get('System', '')
        obsolete_rows.append(f"""
                <tr style="opacity: 0.85;">
                    <td><span style="color: #64748b; font-weight: 500;">{system}</span></td>
                    <td>{app.get('Platform/App', '')}</td>
                    <td>{app.get('Environment', '')}</td>
                    <td>{app.get('Owner', '')}</td>
                </tr>""")
    obsolete_table = '\n'.join(obsolete_rows)
    obsolete_count = len(obsolete_apps)
    
    # Generate deactivated apps table rows
    deactivated_rows = []
    for app in deactivated_apps:
        system = app.get('System', '')
        deactivated_rows.append(f"""
                <tr style="opacity: 0.8;">
                    <td><span style="color: #94a3b8;">{system}</span></td>
                    <td>{app.get('Platform/App', '')}</td>
                    <td>{app.get('Environment', '')}</td>
                    <td>{app.get('Owner', '')}</td>
                </tr>""")
    deactivated_table = '\n'.join(deactivated_rows)
    deactivated_count = len(deactivated_apps)
    
    # ============================================================
    # HTML TEMPLATE - Corporate KPI Dashboard Style
    # ============================================================
    html = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MyID Migration Dashboard</title>
    <!-- 
    ============================================================
    AUTO-GENERATED FILE - Do not edit directly!
    Version: {version}
    Generated by: scripts/generate_dashboard.py
    Generated on: {today}
    Source data: {data_source}
    ============================================================
    -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f0f4f8;
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }}
        
        /* Header */
        .dashboard-header {{
            text-align: center;
            margin-bottom: 25px;
            padding: 25px;
            background: linear-gradient(135deg, {COLORS['primary']} 0%, {COLORS['secondary']} 100%);
            border-radius: 12px;
            color: white;
        }}
        .dashboard-header h1 {{
            font-size: 1.8rem;
            margin-bottom: 8px;
            font-weight: 600;
        }}
        .dashboard-header p {{ opacity: 0.9; font-size: 0.95rem; }}
        .dashboard-header .date {{ opacity: 0.7; font-size: 0.85rem; margin-top: 5px; }}
        
        /* Main Grid Layout */
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}
        
        /* Section Cards */
        .section-card {{
            background: #fff;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e5e9ef;
        }}
        .section-header {{
            padding: 12px 18px;
            font-weight: 600;
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            border-bottom: 1px solid #e5e9ef;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        .section-header .dot {{
            width: 8px;
            height: 8px;
            border-radius: 50%;
        }}
        .section-header.acme {{ background: #e8f4fc; color: {COLORS['primary']}; }}
        .section-header.acme .dot {{ background: {COLORS['primary']}; }}
        .section-header.sentry {{ background: #f3e8fc; color: {COLORS['secondary']}; }}
        .section-header.sentry .dot {{ background: {COLORS['secondary']}; }}
        .section-header.risk {{ background: #fff3e0; color: #e65100; }}
        .section-header.risk .dot {{ background: #ff9800; }}
        .section-header.obsolete {{ background: #f1f5f9; color: {COLORS['obsolete']}; }}
        .section-header.obsolete .dot {{ background: {COLORS['obsolete']}; }}
        .section-body {{
            padding: 18px;
        }}
        
        /* Stat Items in Section */
        .stat-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
        }}
        .stat-item {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 15px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid;
            cursor: pointer;
            transition: all 0.2s ease;
        }}
        .stat-item:hover {{
            background: #f0f4f8;
            transform: translateX(3px);
        }}
        .stat-item .label {{
            font-size: 0.8rem;
            color: #64748b;
            font-weight: 500;
        }}
        .stat-item .value {{
            font-size: 1.5rem;
            font-weight: 700;
        }}
        .stat-item.green {{ border-left-color: {COLORS['done']}; }}
        .stat-item.green .value {{ color: {COLORS['done']}; }}
        .stat-item.amber {{ border-left-color: {COLORS['to_do']}; }}
        .stat-item.amber .value {{ color: {COLORS['to_do']}; }}
        .stat-item.slate {{ border-left-color: {COLORS['obsolete']}; }}
        .stat-item.slate .value {{ color: {COLORS['obsolete']}; }}
        .stat-item.gray {{ border-left-color: {COLORS['na']}; }}
        .stat-item.gray .value {{ color: {COLORS['na']}; }}
        .stat-item.orange {{ border-left-color: {COLORS['at_risk']}; }}
        .stat-item.orange .value {{ color: {COLORS['at_risk']}; }}
        .stat-item.blue {{ border-left-color: {COLORS['in_progress']}; }}
        .stat-item.blue .value {{ color: {COLORS['in_progress']}; }}
        
        /* Total Effort / At Risk Summary */
        .summary-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 10px;
            text-align: center;
        }}
        .summary-item {{
            padding: 15px;
            background: #f8fafc;
            border-radius: 8px;
        }}
        .summary-item .value {{
            font-size: 2rem;
            font-weight: 700;
            color: {COLORS['primary']};
        }}
        .summary-item .label {{
            font-size: 0.75rem;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-top: 5px;
        }}
        
        /* Progress Bar */
        .progress-section {{
            margin-top: 15px;
            padding-top: 15px;
            border-top: 1px solid #e5e9ef;
        }}
        .progress-label {{
            display: flex;
            justify-content: space-between;
            font-size: 0.8rem;
            color: #64748b;
            margin-bottom: 8px;
        }}
        .progress-bar {{
            height: 10px;
            background: #e5e9ef;
            border-radius: 5px;
            overflow: hidden;
        }}
        .progress-fill {{
            height: 100%;
            background: linear-gradient(90deg, {COLORS['done']}, #10b981);
            border-radius: 5px;
            transition: width 0.5s ease;
        }}
        
        /* Charts Row */
        .charts-row {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
            margin-bottom: 25px;
        }}
        .chart-card {{
            background: #fff;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e5e9ef;
        }}
        .chart-card h3 {{
            font-size: 0.9rem;
            color: #475569;
            margin-bottom: 15px;
            font-weight: 600;
        }}
        .chart-container {{ position: relative; height: 250px; }}
        
        /* Tables */
        .table-section {{
            background: #fff;
            border-radius: 12px;
            margin-bottom: 20px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            border: 1px solid #e5e9ef;
            overflow: hidden;
        }}
        .table-header {{
            padding: 15px 20px;
            background: #f8fafc;
            border-bottom: 1px solid #e5e9ef;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}
        .table-header h3 {{
            font-size: 0.95rem;
            color: #334155;
            font-weight: 600;
        }}
        .table-header .badge {{
            background: {COLORS['at_risk']};
            color: white;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.75rem;
            font-weight: 600;
        }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px 20px; text-align: left; border-bottom: 1px solid #e5e9ef; }}
        th {{ background: #f8fafc; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.5px; color: #64748b; }}
        tr:hover {{ background: #f8fafc; }}
        tr:last-child td {{ border-bottom: none; }}
        .status-badge {{ padding: 4px 10px; border-radius: 20px; font-size: 0.75rem; font-weight: 500; }}
        .status-badge.to-do {{ background: #fef3c7; color: #b45309; }}
        .status-badge.done {{ background: #d1fae5; color: #047857; }}
        .status-badge.in-progress {{ background: #dbeafe; color: #1d4ed8; }}
        .status-badge.obsolete {{ background: #f1f5f9; color: #64748b; }}
        .status-badge.not-started {{ background: #fef3c7; color: #b45309; }}
        .status-badge.completed {{ background: #d1fae5; color: #047857; }}
        .clickable-badge {{ cursor: pointer; transition: all 0.2s; }}
        .clickable-badge:hover {{ filter: brightness(0.9); transform: scale(1.05); }}
        .clickable-summary {{ cursor: pointer; transition: all 0.2s; border-radius: 8px; }}
        .clickable-summary:hover {{ background: #eef2f7; transform: translateY(-2px); box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
        
        /* Modal */
        .modal-overlay {{
            display: none;
            position: fixed;
            top: 0; left: 0;
            width: 100%; height: 100%;
            background: rgba(0,0,0,0.6);
            z-index: 1000;
            justify-content: center;
            align-items: center;
            backdrop-filter: blur(4px);
        }}
        .modal-overlay.active {{ display: flex; }}
        .modal {{
            background: #fff;
            border-radius: 16px;
            width: 90%;
            max-width: 700px;
            max-height: 80vh;
            overflow: hidden;
            box-shadow: 0 25px 50px rgba(0,0,0,0.25);
        }}
        .modal-header {{
            padding: 20px 25px;
            border-bottom: 1px solid #e5e9ef;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .modal-header h2 {{ font-size: 1.1rem; color: #334155; display: flex; align-items: center; gap: 12px; }}
        .modal-header .count-badge {{ font-size: 0.8rem; padding: 4px 12px; border-radius: 20px; background: #f1f5f9; color: #64748b; }}
        .modal-close {{
            background: #f1f5f9;
            border: none;
            color: #64748b;
            width: 36px; height: 36px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            transition: all 0.2s;
        }}
        .modal-close:hover {{ background: #e2e8f0; color: #334155; }}
        .modal-body {{ padding: 25px; max-height: 60vh; overflow-y: auto; }}
        .modal-body p.description {{ color: #64748b; font-size: 0.9rem; margin-bottom: 20px; line-height: 1.5; }}
        .modal-app-list {{ display: flex; flex-direction: column; gap: 8px; }}
        .modal-app-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            background: #f8fafc;
            border-radius: 8px;
            border-left: 4px solid;
        }}
        .modal-app-item .app-name {{ font-weight: 500; color: #334155; font-size: 0.9rem; }}
        .modal-app-item .app-meta {{ display: flex; gap: 15px; font-size: 0.75rem; color: #64748b; }}
        .modal-app-item.green {{ border-left-color: {COLORS['done']}; }}
        .modal-app-item.amber {{ border-left-color: {COLORS['to_do']}; }}
        .modal-app-item.blue {{ border-left-color: {COLORS['in_progress']}; }}
        .modal-app-item.slate {{ border-left-color: {COLORS['obsolete']}; }}
        .modal-app-item.gray {{ border-left-color: {COLORS['na']}; }}
        .modal-app-item.orange {{ border-left-color: {COLORS['at_risk']}; }}
        
        .footer {{ text-align: center; padding: 20px; color: #94a3b8; font-size: 0.8rem; }}
        
        @media (max-width: 1200px) {{ .main-grid {{ grid-template-columns: 1fr 1fr; }} }}
        @media (max-width: 768px) {{ .main-grid, .charts-row {{ grid-template-columns: 1fr; }} }}
        
        @media print {{
            body {{ padding: 0; background: white; -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            .dashboard-header {{ border-radius: 0; margin-bottom: 15px; padding: 15px; }}
            .section-card, .chart-card, .table-section {{ box-shadow: none; break-inside: avoid; page-break-inside: avoid; }}
            .main-grid {{ gap: 12px; margin-bottom: 15px; }}
            .charts-row {{ gap: 12px; margin-bottom: 15px; }}
            .modal-overlay {{ display: none !important; }}
            .stat-item {{ cursor: default; }}
            .stat-item:hover {{ transform: none; }}
            .clickable-badge {{ cursor: default; }}
            .clickable-badge:hover {{ transform: none; filter: none; }}
            .clickable-summary:hover {{ transform: none; box-shadow: none; }}
            .table-section {{ margin-bottom: 15px; }}
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>MyID Migration Dashboard</h1>
        <p>SOLO → ACME & Sentry 1.0 → Sentry 2.0 Migration Tracking</p>
        <p class="date">{version} • Last Updated: {today}</p>
    </div>

    <div class="main-grid">
        <!-- ACME Migration Summary (SOLO → ACME) -->
        <div class="section-card">
            <div class="section-header acme">
                <span class="dot"></span>
                SOLO → ACME Migration
    </div>
            <div class="section-body">
                <div class="stat-grid">
                    <div class="stat-item green" onclick="showModal('acme-done')">
                        <span class="label">Done</span>
                        <span class="value">{stats['acme_done']}</span>
        </div>
                    <div class="stat-item blue" onclick="showModal('acme-in-progress')">
                        <span class="label">In Progress</span>
                        <span class="value">{stats['acme_in_progress']}</span>
        </div>
                    <div class="stat-item amber" onclick="showModal('acme-to-do')">
                        <span class="label">To Do</span>
                        <span class="value">{stats['acme_to_do']}</span>
        </div>
                    <div class="stat-item orange" onclick="showModal('at-risk')">
                        <span class="label">At Risk 2/27</span>
                        <span class="value">{stats['at_risk']}</span>
                    </div>
                </div>
                <div class="progress-section">
                    <div class="progress-label">
                        <span>Off SOLO Progress</span>
                        <span>{progress_pct}% ({stats['acme_done']} of {acme_requiring_migration})</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {progress_pct}%"></div>
                    </div>
                </div>
        </div>
    </div>

        <!-- Sentry Migration Summary (1.0 → 2.0/Direct Int/Debut-Sentry) -->
        <div class="section-card">
            <div class="section-header sentry">
                <span class="dot"></span>
                Sentry 1.0 → Off Sentry 1.0
    </div>
            <div class="section-body">
                <div class="stat-grid">
                    <div class="stat-item green" onclick="showModal('sentry-done')">
                        <span class="label">Done</span>
                        <span class="value">{stats['sentry_done']}</span>
        </div>
                    <div class="stat-item blue" onclick="showModal('sentry-in-progress')">
                        <span class="label">In Progress</span>
                        <span class="value">{stats['sentry_in_progress']}</span>
        </div>
                    <div class="stat-item amber" onclick="showModal('sentry-to-do')">
                        <span class="label">To Do</span>
                        <span class="value">{stats['sentry_to_do']}</span>
        </div>
                    <div class="stat-item gray" onclick="showModal('sentry-na')">
                        <span class="label">N/A (SOLO Apps)</span>
                        <span class="value">{stats['sentry_na']}</span>
                    </div>
                </div>
                <div class="progress-section">
                    <div class="progress-label">
                        <span>Off Sentry 1.0 Progress</span>
                        <span>{sentry_progress_pct}% ({stats['sentry_done']} of {sentry_requiring_migration})</span>
                    </div>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: {sentry_progress_pct}%; background: linear-gradient(90deg, #7c3aed, #a855f7);"></div>
                    </div>
                </div>
        </div>
    </div>

        <!-- Summary Overview -->
        <div class="section-card">
            <div class="section-header risk">
                <span class="dot"></span>
                Overview & Risk (2/27/26)
            </div>
            <div class="section-body">
                <div class="summary-grid">
                    <div class="summary-item clickable-summary" onclick="showOverviewModal('active')">
                        <div class="value">{stats['total']}</div>
                        <div class="label">Active Apps</div>
        </div>
                    <div class="summary-item clickable-summary" onclick="showModal('at-risk')">
                        <div class="value" style="color: {COLORS['at_risk']};">{stats['at_risk']}</div>
                        <div class="label">At Risk</div>
                    </div>
                    <div class="summary-item clickable-summary" onclick="showOverviewModal('obsolete')">
                        <div class="value" style="color: {COLORS['obsolete']};">{obsolete_count}</div>
                        <div class="label">Obsolete</div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- System Migration Quadrant Section -->
    <div class="table-section" style="margin-bottom: 25px;">
        <div class="table-header">
            <h3>System Migration Quadrant</h3>
            <span class="badge" style="background: {COLORS['primary']};">{len(system_names)} Systems</span>
        </div>
        <div style="display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 20px; padding: 20px;">
            <!-- Quadrant Chart -->
            <div>
                <div style="position: relative; height: 350px;">
                    <canvas id="quadrantChart"></canvas>
                </div>
                <div style="margin-top: 10px; display: flex; gap: 15px; justify-content: center; flex-wrap: wrap; font-size: 0.75rem; color: #64748b;">
                    <span><span style="display: inline-block; width: 12px; height: 12px; background: #dc2626; border-radius: 50%; vertical-align: middle;"></span> Needs both migrations</span>
                    <span><span style="display: inline-block; width: 12px; height: 12px; background: #f59e0b; border-radius: 50%; vertical-align: middle;"></span> Partial progress</span>
                    <span><span style="display: inline-block; width: 12px; height: 12px; background: #059669; border-radius: 50%; vertical-align: middle;"></span> Fully migrated</span>
                </div>
            </div>
            <!-- Summary Table -->
            <div>
                <h4 style="font-size: 0.85rem; color: #475569; margin-bottom: 15px; font-weight: 600;">Migration Status by System</h4>
                <table style="font-size: 0.8rem;">
                    <thead>
                        <tr>
                            <th>System</th>
                            <th style="text-align: center;">Apps</th>
                            <th style="text-align: center;">Off SOLO</th>
                            <th style="text-align: center;">Off Sentry 1</th>
                        </tr>
                    </thead>
                    <tbody>{system_summary_table}
                    </tbody>
                </table>
            </div>
        </div>
    </div>

    <!-- Charts Row -->
    <div class="charts-row">
        <div class="chart-card">
            <h3>SOLO → ACME Migration Status</h3>
            <div class="chart-container">
                <canvas id="acmeChart"></canvas>
            </div>
        </div>
        <div class="chart-card">
            <h3>Work Distribution by Tech Lead</h3>
            <div class="chart-container">
                <canvas id="techLeadChart"></canvas>
            </div>
        </div>
    </div>

    <!-- At Risk Table -->
    <div class="table-section">
        <div class="table-header">
            <h3>At Risk for 2/27/26 Deadline</h3>
            <span class="badge">{stats['at_risk']} Items</span>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Platform/App</th>
                    <th>Env</th>
                    <th>System</th>
                    <th>Tech Lead</th>
                    <th>ACME Status</th>
                    <th>Sentry Status</th>
                    <th>JIRA</th>
                </tr>
            </thead>
            <tbody>{at_risk_table}
            </tbody>
        </table>
    </div>

    <!-- Future Work Table -->
    <div class="table-section">
        <div class="table-header">
            <h3>Future Migrations (No Deadline)</h3>
            <span class="badge" style="background: {COLORS['to_do']}; color: #000;">{len(groups['future'])} Items</span>
        </div>
        <table>
            <thead>
                <tr>
                    <th>Platform/App</th>
                    <th>Env</th>
                    <th>System</th>
                    <th>Tech Lead</th>
                    <th>Status</th>
                    <th>JIRA</th>
                </tr>
            </thead>
            <tbody>{future_table}
            </tbody>
        </table>
    </div>

    <!-- Obsolete Apps Reference Section -->
    <div class="table-section" style="margin-top: 30px;">
        <div class="table-header" style="background: #f1f5f9;">
            <h3 style="color: {COLORS['obsolete']};">Obsolete Apps (No Migration Required)</h3>
            <span class="badge" style="background: {COLORS['obsolete']};">{obsolete_count} Items</span>
        </div>
        <div style="padding: 12px 20px; background: #f8fafc; border-bottom: 1px solid #e5e9ef; font-size: 0.8rem; color: #64748b;">
            <em>These apps are marked as Obsolete and are excluded from all migration statistics and system totals.</em>
        </div>
        <table>
            <thead>
                <tr>
                    <th>System</th>
                    <th>Platform/App</th>
                    <th>Env</th>
                    <th>Owner</th>
                </tr>
            </thead>
            <tbody>{obsolete_table}
            </tbody>
        </table>
    </div>

    <!-- Deactivated Apps Section -->
    <div class="table-section" style="margin-top: 20px; opacity: 0.85;">
        <div class="table-header" style="background: #f1f5f9;">
            <h3 style="color: #94a3b8;">Deactivated Apps (Not in Use)</h3>
            <span class="badge" style="background: #94a3b8;">{deactivated_count} Items</span>
        </div>
        <div style="padding: 12px 20px; background: #f8fafc; border-bottom: 1px solid #e5e9ef; font-size: 0.8rem; color: #64748b;">
            <em>These apps are marked as "Not in Use" and are excluded from migration statistics.</em>
        </div>
        <table>
            <thead>
                <tr>
                    <th>System</th>
                    <th>Platform/App</th>
                    <th>Env</th>
                    <th>Owner</th>
                </tr>
            </thead>
            <tbody>{deactivated_table}
            </tbody>
        </table>
    </div>

    <div class="footer">
        <p>MyID Migration Dashboard {version} • Auto-generated from {data_source} on {today}</p>
    </div>

    <!-- Modal -->
    <div class="modal-overlay" id="modal-overlay" onclick="closeModal(event)">
        <div class="modal" onclick="event.stopPropagation()">
            <div class="modal-header">
                <h2 id="modal-title">Title</h2>
                <button class="modal-close" onclick="closeModal()">✕</button>
            </div>
            <div class="modal-body" id="modal-body"></div>
        </div>
    </div>

    <script>
        const modalData = {{{modal_data_js}
        }};

        function showModal(type) {{
            const data = modalData[type];
            if (!data) return;

            const overlay = document.getElementById('modal-overlay');
            const title = document.getElementById('modal-title');
            const body = document.getElementById('modal-body');

            title.innerHTML = `<span style="color: ${{data.titleColor}}">●</span> ${{data.title}} <span class="count-badge">${{data.count}} apps</span>`;

            let html = `<p class="description">${{data.description}}</p>`;
            
            if (data.note) {{
                html += `<p style="background: #fef3c7; padding: 12px; border-radius: 8px; border-left: 3px solid #f59e0b; margin-bottom: 20px; font-size: 0.85rem; color: #92400e;">${{data.note}}</p>`;
            }}

            html += '<div class="modal-app-list">';
            
            data.apps.forEach(app => {{
                let meta = `<span>${{app.env}}</span><span>${{app.system}}</span>`;
                if (app.lead) meta += `<span>Lead: ${{app.lead}}</span>`;
                if (app.deadline) meta += `<span style="color: #0ea5e9;">Deadline: ${{app.deadline}}</span>`;
                if (app.blocker) meta = `<span style="color: #dc2626;">⚠ ${{app.blocker}}</span>`;
                if (app.reason) meta += `<span>${{app.reason}}</span>`;
                if (app.status) meta += `<span>${{app.status}}</span>`;
                if (app.auth) meta += `<span>Auth: ${{app.auth}}</span>`;
                if (app.jira) meta += `<span style="color: #0ea5e9;">JIRA: ${{app.jira}}</span>`;
                if (app.acme) meta += `<span>ACME: ${{app.acme}}</span>`;
                if (app.sentry) meta += `<span>Sentry: ${{app.sentry}}</span>`;

                html += `
                    <div class="modal-app-item ${{data.color}}">
                        <span class="app-name">${{app.name}}</span>
                        <div class="app-meta">${{meta}}</div>
                    </div>
                `;
            }});

            html += '</div>';
            body.innerHTML = html;

            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        function closeModal(event) {{
            if (event && event.target !== event.currentTarget) return;
            document.getElementById('modal-overlay').classList.remove('active');
            document.body.style.overflow = '';
        }}

        document.addEventListener('keydown', (e) => {{
            if (e.key === 'Escape') closeModal();
        }});

        // Per-system modal data for clickable badges
        const systemModalData = {{{system_modal_js}
        }};

        function showSystemModal(key) {{
            const data = systemModalData[key];
            if (!data) return;

            const overlay = document.getElementById('modal-overlay');
            const title = document.getElementById('modal-title');
            const body = document.getElementById('modal-body');

            title.innerHTML = `<span style="color: ${{data.titleColor}}">●</span> ${{data.title}} <span class="count-badge">${{data.systemSummary}}</span>`;

            let html = '';

            if (data.remaining.length > 0) {{
                html += `<p style="font-weight: 600; color: #b45309; margin-bottom: 10px; font-size: 0.9rem;">⚠ Remaining (${{data.remaining.length}})</p>`;
                html += '<div class="modal-app-list" style="margin-bottom: 20px;">';
                data.remaining.forEach(app => {{
                    html += `
                        <div class="modal-app-item amber">
                            <span class="app-name">${{app.name}}</span>
                            <div class="app-meta">
                                <span>${{app.env}}</span>
                                <span>ACME: ${{app.acmeStatus}}</span>
                                <span>Sentry: ${{app.sentryStatus}}</span>
                                ${{app.jira ? '<span style="color: #0ea5e9;">JIRA: ' + app.jira + '</span>' : ''}}
                            </div>
                        </div>`;
                }});
                html += '</div>';
            }}

            if (data.done.length > 0) {{
                html += `<p style="font-weight: 600; color: #047857; margin-bottom: 10px; font-size: 0.9rem;">✓ Done (${{data.done.length}})</p>`;
                html += '<div class="modal-app-list">';
                data.done.forEach(app => {{
                    html += `
                        <div class="modal-app-item green">
                            <span class="app-name">${{app.name}}</span>
                            <div class="app-meta">
                                <span>${{app.env}}</span>
                                ${{app.auth ? '<span>Auth: ' + app.auth + '</span>' : ''}}
                                ${{app.jira ? '<span style="color: #0ea5e9;">JIRA: ' + app.jira + '</span>' : ''}}
                            </div>
                        </div>`;
                }});
                html += '</div>';
            }}

            if (data.done.length === 0 && data.remaining.length === 0) {{
                html = '<p style="color: #94a3b8; font-style: italic;">No apps in this category.</p>';
            }}

            body.innerHTML = html;
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        // Overview modal data
        const overviewData = {{
            active: [
                {active_apps_js}
            ],
            obsolete: [
                {obsolete_apps_js}
            ]
        }};

        function showOverviewModal(type) {{
            const overlay = document.getElementById('modal-overlay');
            const title = document.getElementById('modal-title');
            const body = document.getElementById('modal-body');

            if (type === 'active') {{
                const apps = overviewData.active;
                title.innerHTML = `<span style="color: {COLORS['primary']}">●</span> Active Apps <span class="count-badge">${{apps.length}} apps</span>`;
                let html = '<p class="description">All non-obsolete applications currently being tracked for migration.</p>';
                html += '<div class="modal-app-list">';
                apps.forEach(app => {{
                    const acmeColor = app.acme === 'Done' ? 'green' : (app.acme === 'In Progress' ? 'blue' : 'amber');
                    html += `
                        <div class="modal-app-item ${{acmeColor}}">
                            <span class="app-name">${{app.name}}</span>
                            <div class="app-meta">
                                <span>${{app.env}}</span>
                                <span>${{app.system}}</span>
                                <span>ACME: ${{app.acme}}</span>
                                <span>Sentry: ${{app.sentry}}</span>
                            </div>
                        </div>`;
                }});
                html += '</div>';
                body.innerHTML = html;
            }} else if (type === 'obsolete') {{
                const apps = overviewData.obsolete;
                title.innerHTML = `<span style="color: {COLORS['obsolete']}">●</span> Obsolete Apps <span class="count-badge">${{apps.length}} apps</span>`;
                let html = '<p class="description">These apps are marked as Obsolete — no migration required. They are excluded from all statistics.</p>';
                html += '<div class="modal-app-list">';
                apps.forEach(app => {{
                    html += `
                        <div class="modal-app-item slate">
                            <span class="app-name">${{app.name}}</span>
                            <div class="app-meta">
                                <span>${{app.system}}</span>
                                <span>Owner: ${{app.owner}}</span>
                            </div>
                        </div>`;
                }});
                html += '</div>';
                body.innerHTML = html;
            }}

            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        }}

        const colors = {{
            done: '{COLORS["done"]}',
            toDo: '{COLORS["to_do"]}',
            inProgress: '{COLORS["in_progress"]}',
            obsolete: '{COLORS["obsolete"]}',
            na: '{COLORS["na"]}'
        }};

        // ACME Doughnut Chart (SOLO → ACME)
        new Chart(document.getElementById('acmeChart').getContext('2d'), {{
            type: 'doughnut',
            data: {{
                labels: ['Done', 'In Progress', 'To Do'],
                datasets: [{{
                    data: [{stats['acme_done']}, {stats['acme_in_progress']}, {stats['acme_to_do']}],
                    backgroundColor: [colors.done, colors.inProgress, colors.toDo],
                    borderWidth: 0
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#64748b', padding: 15, usePointStyle: true, font: {{ size: 11 }} }} }} }},
                cutout: '65%'
            }}
        }});

        // Tech Lead Workload Chart
        new Chart(document.getElementById('techLeadChart').getContext('2d'), {{
            type: 'bar',
            data: {{
                labels: {tech_leads},
                datasets: [
                    {{ label: 'Done', data: {done_data}, backgroundColor: colors.done }},
                    {{ label: 'In Progress', data: {in_progress_data}, backgroundColor: colors.inProgress }},
                    {{ label: 'To Do', data: {to_do_data}, backgroundColor: colors.toDo }}
                ]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{ stacked: true, grid: {{ display: false }}, ticks: {{ color: '#64748b', font: {{ size: 10 }} }} }},
                    y: {{ stacked: true, grid: {{ color: 'rgba(0,0,0,0.05)' }}, ticks: {{ color: '#64748b' }} }}
                }},
                plugins: {{ legend: {{ position: 'bottom', labels: {{ color: '#64748b', padding: 15, usePointStyle: true, font: {{ size: 11 }} }} }} }}
            }}
        }});

        // System Migration Quadrant Chart (Bubble Chart)
        const quadrantData = {quadrant_bubbles_js};
        
        // Custom plugin to draw 6-cell quadrant backgrounds and labels
        // Layout: Sentry 1.0 (top) → Debut Sentry (middle) → Sentry 2.0 (bottom)
        //         SOLO (left) → ACME (right)
        const quadrantPlugin = {{
            id: 'quadrantBackground',
            beforeDraw: (chart) => {{
                const ctx = chart.ctx;
                const chartArea = chart.chartArea;
                const midX = (chartArea.left + chartArea.right) / 2;
                const height = chartArea.bottom - chartArea.top;
                const thirdH = height / 3;
                const topY = chartArea.top;
                const midTopY = chartArea.top + thirdH;      // Between Sentry 1.0 and Debut
                const midBotY = chartArea.top + 2 * thirdH;  // Between Debut and Sentry 2.0
                const botY = chartArea.bottom;
                
                // === TOP ROW: Sentry 1.0 ===
                // Top-left: SOLO + Sentry 1.0 (Starting Point - red)
                ctx.fillStyle = 'rgba(220, 38, 38, 0.10)';
                ctx.fillRect(chartArea.left, topY, midX - chartArea.left, thirdH);
                
                // Top-right: ACME + Sentry 1.0 (Partial - amber)
                ctx.fillStyle = 'rgba(245, 158, 11, 0.08)';
                ctx.fillRect(midX, topY, chartArea.right - midX, thirdH);
                
                // === MIDDLE ROW: Debut Sentry ===
                // Middle-left: SOLO + Debut Sentry (amber)
                ctx.fillStyle = 'rgba(245, 158, 11, 0.06)';
                ctx.fillRect(chartArea.left, midTopY, midX - chartArea.left, thirdH);
                
                // Middle-right: ACME + Debut Sentry (VPP Goal - light green)
                ctx.fillStyle = 'rgba(5, 150, 105, 0.10)';
                ctx.fillRect(midX, midTopY, chartArea.right - midX, thirdH);
                
                // === BOTTOM ROW: Sentry 2.0 ===
                // Bottom-left: SOLO + Sentry 2.0 (amber)
                ctx.fillStyle = 'rgba(245, 158, 11, 0.06)';
                ctx.fillRect(chartArea.left, midBotY, midX - chartArea.left, thirdH);
                
                // Bottom-right: ACME + Sentry 2.0 (Full Goal - green)
                ctx.fillStyle = 'rgba(5, 150, 105, 0.15)';
                ctx.fillRect(midX, midBotY, chartArea.right - midX, thirdH);
                
                // === LABELS ===
                ctx.font = '10px -apple-system, BlinkMacSystemFont, sans-serif';
                ctx.textAlign = 'center';
                
                // Top-left label (Starting Point)
                ctx.fillStyle = '#dc2626';
                ctx.fillText('SOLO + Sentry 1.0', (chartArea.left + midX) / 2, topY + 15);
                ctx.fillText('(Starting Point)', (chartArea.left + midX) / 2, topY + 28);
                
                // Top-right label
                ctx.fillStyle = '#b45309';
                ctx.fillText('ACME + Sentry 1.0', (midX + chartArea.right) / 2, topY + 20);
                
                // Middle-right label (VPP Goal)
                ctx.fillStyle = '#047857';
                ctx.font = 'bold 10px -apple-system, BlinkMacSystemFont, sans-serif';
                ctx.fillText('ACME + Debut Sentry', (midX + chartArea.right) / 2, midTopY + 15);
                ctx.fillText('(VPP Goal)', (midX + chartArea.right) / 2, midTopY + 28);
                
                // Bottom-right label (Main Goal)
                ctx.fillStyle = '#047857';
                ctx.font = 'bold 10px -apple-system, BlinkMacSystemFont, sans-serif';
                ctx.fillText('ACME + Sentry 2.0', (midX + chartArea.right) / 2, midBotY + 15);
                ctx.fillText('✓ GOAL', (midX + chartArea.right) / 2, midBotY + 28);
                
                // === GRID LINES ===
                ctx.strokeStyle = '#cbd5e1';
                ctx.lineWidth = 1;
                ctx.setLineDash([5, 5]);
                
                // Vertical line (50% ACME)
                ctx.beginPath();
                ctx.moveTo(midX, topY);
                ctx.lineTo(midX, botY);
                ctx.stroke();
                
                // Horizontal lines (Sentry tiers)
                ctx.beginPath();
                ctx.moveTo(chartArea.left, midTopY);
                ctx.lineTo(chartArea.right, midTopY);
                ctx.stroke();
                
                ctx.beginPath();
                ctx.moveTo(chartArea.left, midBotY);
                ctx.lineTo(chartArea.right, midBotY);
                ctx.stroke();
                
                ctx.setLineDash([]);
            }}
        }};
        
        // Create datasets - one per system for individual colors
        const bubbleDatasets = quadrantData.map((item, idx) => ({{
            label: item.label,
            data: [{{ x: item.x, y: item.y, r: item.r }}],
            backgroundColor: item.color + 'cc',
            borderColor: item.color,
            borderWidth: 2
        }}));
        
        const quadrantChart = new Chart(document.getElementById('quadrantChart').getContext('2d'), {{
            type: 'bubble',
            data: {{ datasets: bubbleDatasets }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    x: {{
                        min: 0,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'SOLO ←――――――――――――――――――――――――――→ ACME',
                            color: '#475569',
                            font: {{ size: 12, weight: '600' }}
                        }},
                        ticks: {{
                            callback: (val) => val + '%',
                            color: '#64748b',
                            stepSize: 25
                        }},
                        grid: {{ color: 'rgba(0,0,0,0.05)' }}
                    }},
                    y: {{
                        min: 0,
                        max: 100,
                        title: {{
                            display: true,
                            text: 'Sentry 2.0 (Goal) ←―――――――――→ Sentry 1.0',
                            color: '#475569',
                            font: {{ size: 12, weight: '600' }}
                        }},
                        ticks: {{
                            callback: function(val) {{
                                if (val === 100) return 'Sentry 1.0';
                                if (val === 50) return 'Debut Sentry';
                                if (val === 0) return 'Sentry 2.0';
                                return '';
                            }},
                            color: '#64748b',
                            stepSize: 50
                        }},
                        grid: {{ color: 'rgba(0,0,0,0.08)' }}
                    }}
                }},
                plugins: {{
                    legend: {{ display: false }},
                    tooltip: {{
                        backgroundColor: 'rgba(255,255,255,0.95)',
                        titleColor: '#1e293b',
                        bodyColor: '#475569',
                        borderColor: '#e2e8f0',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: false,
                        callbacks: {{
                            title: function(context) {{
                                const item = quadrantData[context[0].datasetIndex];
                                return item.label + ' (' + item.total + ' apps)';
                            }},
                            label: function(context) {{
                                const item = quadrantData[context.datasetIndex];
                                // Use actual percentages (off_solo_pct, off_sentry1_pct), NOT display x/y positions
                                const soloLine = item.off_solo_pct >= 100
                                    ? '✓ Fully off SOLO'
                                    : (item.off_solo_pct > 0
                                        ? '◐ Partially off SOLO (' + item.off_solo_pct + '%)'
                                        : '○ Still on SOLO');
                                let sentryLine;
                                if (item.solo_only) {{
                                    sentryLine = '— N/A (no Sentry)';
                                }} else if (item.off_sentry1_pct >= 100) {{
                                    sentryLine = '✓ Fully off Sentry 1.0';
                                }} else if (item.off_sentry1_pct > 0) {{
                                    sentryLine = '◐ Partially off Sentry 1.0 (' + item.off_sentry1_pct + '%)';
                                }} else {{
                                    sentryLine = '○ Still on Sentry 1.0';
                                }}
                                return [
                                    '─────────────────────',
                                    'ACME: ' + item.acme_display,
                                    'Sentry: ' + item.sentry_display,
                                    '─────────────────────',
                                    soloLine,
                                    sentryLine
                                ];
                            }}
                        }}
                    }}
                }}
            }},
            plugins: [quadrantPlugin, {{
                // Plugin to draw labels on bubbles
                afterDraw: (chart) => {{
                    const ctx = chart.ctx;
                    ctx.font = 'bold 10px -apple-system, BlinkMacSystemFont, sans-serif';
                    ctx.textAlign = 'center';
                    ctx.textBaseline = 'middle';
                    
                    chart.data.datasets.forEach((dataset, i) => {{
                        const meta = chart.getDatasetMeta(i);
                        meta.data.forEach((bubble) => {{
                            ctx.fillStyle = '#fff';
                            ctx.fillText(quadrantData[i].label, bubble.x, bubble.y);
                        }});
                    }});
                }}
            }}]
        }});
    </script>
</body>
</html>'''
    
    return html

def main():
    """
    ============================================================
    MAIN FUNCTION
    ============================================================
    """
    print("=" * 60)
    print("MyID Migration Dashboard Generator")
    print("=" * 60)
    
    # Read data (auto-detects most recent Excel file)
    try:
        all_apps, data_source, data_file_path = read_data()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        return
    
    # Filter out deactivated apps (marked as "Not in use")
    apps_after_deactivated, deactivated_apps = filter_deactivated_apps(all_apps)
    
    # Separate Obsolete apps from active apps
    # Obsolete apps are excluded from ALL statistics and system totals
    active_apps = []
    obsolete_apps = []
    for app in apps_after_deactivated:
        acme_status = app.get('ACME Migration Status', '')
        if acme_status == 'Obsolete':
            obsolete_apps.append(app)
        else:
            active_apps.append(app)
    
    print(f"Found {len(all_apps)} total applications")
    print(f"  - Active: {len(active_apps)}")
    print(f"  - Obsolete: {len(obsolete_apps)}")
    print(f"  - Deactivated: {len(deactivated_apps)}")
    
    # Calculate statistics (only for non-obsolete active apps)
    stats = calculate_stats(active_apps)
    print(f"\nACME Migration Stats (SOLO → ACME):")
    print(f"  - Done: {stats['acme_done']}")
    print(f"  - In Progress: {stats['acme_in_progress']}")
    print(f"  - To Do: {stats['acme_to_do']}")
    print(f"  - At Risk: {stats['at_risk']}")
    print(f"\nSentry Migration Stats (Sentry 1.0 → Off):")
    print(f"  - Done: {stats['sentry_done']}")
    print(f"  - In Progress: {stats['sentry_in_progress']}")
    print(f"  - To Do: {stats['sentry_to_do']}")
    print(f"  - N/A: {stats['sentry_na']}")
    
    # Update version (auto-increments if data file changed)
    version = update_version_if_needed(data_file_path, stats)
    print(f"\nDashboard Version: {version}")
    
    # Group apps (only non-obsolete active apps)
    groups = group_apps_by_status(active_apps)
    
    # Calculate workload (only non-obsolete active apps)
    workload = calculate_tech_lead_workload(active_apps)
    
    # Calculate system migration matrix (only non-obsolete active apps)
    system_matrix = calculate_system_migration_matrix(active_apps)
    
    # Generate HTML
    html = generate_html(stats, groups, workload, system_matrix, active_apps, obsolete_apps, deactivated_apps, data_source, version)
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Write output
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"\nDashboard generated: {OUTPUT_PATH}")
    print(f"Changelog updated: {CHANGELOG_PATH}")
    print("=" * 60)
    print("Done! Open the HTML file in your browser to view.")
    print("=" * 60)

if __name__ == "__main__":
    main()
