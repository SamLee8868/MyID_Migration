# MyID Migration Dashboard - Project Context

**Last Updated:** February 17, 2026 (Session 3 - Versioning & Quadrant Fixes)

**Purpose:** This file captures ALL context needed to continue work on this project. Point a new AI agent to this file to restore full context.

---

## Quick Start for New Session

Say this to the AI:
> "Read `/Users/sam.levine.-nd/Desktop/2026 Projects/MyID_Migration/docs/PROJECT_CONTEXT.md` and be ready to continue work on the MyID Migration Dashboard."

---

## Project Overview

**Two INDEPENDENT Migration Tracks:**
1. **SOLO → ACME** (MyID authentication system upgrade)
2. **Sentry 1.0 → Off Sentry 1.0** (migrate to Sentry 2.0, Direct Integration, or Debut-Sentry)

**Key Deadline:** 2/27/26 (6 apps at risk for ACME migration)

**Current Status (as of Feb 17, 2026) - Dashboard v2.1:**
- **Active Apps:** 29 (non-obsolete, in-use applications)
- **Obsolete Apps:** 12 (no migration required - excluded from all stats)
- **Deactivated Apps:** 12 (marked "not in use" - excluded from stats)
- **ACME:** 10 Done, 19 To Do, 0 In Progress, 6 At Risk
- **Sentry:** 21 Done, 0 To Do, 5 In Progress, 3 N/A

---

## File Structure

```
/Users/sam.levine.-nd/Desktop/2026 Projects/MyID_Migration/
├── data/
│   ├── input/
│   │   └── *.xlsx                      # Excel files (script auto-detects newest)
│   └── version_state.json              # Version tracking (auto-generated)
├── docs/
│   └── PROJECT_CONTEXT.md              # THIS FILE - Read this to restore context
├── reports/
│   └── MyID_Migration_Dashboard.html   # Generated dashboard (auto-created)
├── scripts/
│   └── generate_dashboard.py           # Dashboard generator script
├── CHANGELOG.md                         # Version history (auto-updated)
└── README.md                            # User guide
```

**CRITICAL:** Script auto-detects the most recent `.xlsx` file in `data/input/`. Add date suffix like `_MMDDYY` when downloading from SharePoint.

---

## Daily Workflow

```bash
# 1. Download Excel from SharePoint (add date suffix like _MMDDYY)
#    Save to: data/input/

# 2. Generate dashboard (auto-detects newest Excel file)
cd "/Users/sam.levine.-nd/Desktop/2026 Projects/MyID_Migration"
python3 scripts/generate_dashboard.py

# 3. View dashboard
open reports/MyID_Migration_Dashboard.html
```

**Versioning:**
- Minor version auto-increments when data file changes (v2.1 → v2.2)
- Major version: Edit `DASHBOARD_MAJOR_VERSION` in script (line 55)
- CHANGELOG.md auto-updated with each version change

---

## Excel File Structure (v3 Format)

**File:** `MP&A_-_Okta-Based_MyID_Migration_(SOLO to ACME)_v3.xlsx`

**Row 0:** Section headers (merged cells)  
**Row 1:** Column headers  
**Row 2+:** Data rows

### Column Mapping

| Col | Name | Values | Purpose |
|-----|------|--------|---------|
| A | Platform/App | Text | App name/environment (e.g., "fgs-saml-stg") |
| B | System | Text | System name (BzBee, FGS, GSS, Genie, TM, VPP, Workforce) |
| C | POC | Text | Owner/Tech Lead |
| D | Obsolete | ✓/x | ✓ = No migration required (excluded from stats) |
| E | Sentry 1.0 | ✓/x | Currently on Sentry 1.0 |
| F | Sentry 2.0 | ✓/x | Currently on Sentry 2.0 |
| G | Direct Integration | ✓/x | Currently on Direct Integration |
| H | Debut-Sentry | ✓/x | Currently on Debut-Sentry |
| I | Auth Sys Status | Text | Auth system migration status (Done/In Progress/To Do) |
| J | SOLO | ✓/x | Currently on SOLO |
| K | ACME | ✓/x | Currently on ACME |
| L | Migration Status | Text | Overall ACME migration status (Done/In Progress/To Do/Obsolete) |
| M | Infra Access | Text | Infrastructure access status |
| N | Due Date | Serial | Excel date serial (e.g., 45698 = 02/27/2026) |
| O | Future | Text | Future migration flag |
| P | JIRA | Text | JIRA ticket number |
| Q | Notes | Text | **EXCLUDED from dashboard** (user reference only) |

### Legend (Critical for Data Interpretation)

```
✓  = Yes
x  = No
n/a = Not Applicable
?  = Unknown
Obsolete = No migration required
```

### Status Values (Column L - Migration Status)

**Valid values ONLY:**
- `Done` - Migration completed
- `In Progress` - Currently migrating
- `To Do` - Not yet started
- `Obsolete` - No migration needed

**DO NOT USE:** "Blocked", "Not Started", "Completed", "Not Needed" (old terminology)

---

## Data Logic Rules (CRITICAL - DO NOT BREAK THESE)

### Obsolete Detection
An app is **Obsolete** if:
- Column D (Obsolete) = ✓ **OR**
- Column L (Migration Status) = "Obsolete"

**Obsolete apps are:**
- Excluded from ALL statistics
- Excluded from system totals
- Excluded from charts
- Shown ONLY in a reference table at bottom of dashboard

### ACME Migration Status (SOLO → ACME Track)
**Primary source:** Column L (Migration Status)  
**Secondary:** Column K (ACME column)

Logic:
1. If Obsolete → "Obsolete"
2. Else if L = "Done" → "Done"
3. Else if K = ✓ → "Done" (already on ACME)
4. Else if L = "In Progress" → "In Progress"
5. Else if L = "To Do" → "To Do"
6. Else → "To Do"

### Sentry Migration Status (Sentry 1.0 → Off Sentry 1.0)
**Off Sentry 1.0** means: ✓ in **any** of F/G/H (Sentry 2.0, Direct Integration, or Debut-Sentry)

Logic:
1. If Obsolete → "Obsolete"
2. Else if F = ✓ OR G = ✓ OR H = ✓ → "Done"
3. Else if E = ✓ (still on Sentry 1.0):
   - Check Column I (Auth Sys Status) for Done/In Progress/To Do
4. Else if all E/F/G/H = n/a or x → "N/A" (no Sentry involvement)

**IMPORTANT:** Only ONE of E/F/G/H will have ✓ (mutually exclusive).

### System Matrix (Migration Status by System)

Two independent tracks calculated separately:

**OFF SOLO:**
- Count apps where ACME status = "Done"
- Percentage: (Done / Total active apps in system) * 100

**OFF SENTRY 1.0:**
- Count apps where Sentry status = "Done"
- Only count apps that USE Sentry (exclude N/A apps)
- Percentage: (Done / Total Sentry-using apps in system) * 100
- If no apps use Sentry → show "N/A (SOLO)"

---

## Dashboard Features

### Layout Order
1. **KPI Cards** (3 columns)
   - SOLO → ACME Migration (Done/In Progress/To Do/At Risk)
   - Sentry 1.0 → Off (Done/In Progress/To Do/N/A)
   - Overview & Risk (Active Apps/At Risk/Obsolete) - **all clickable**
2. **System Migration Quadrant** (bubble chart + table)
   - Bubble chart: Systems positioned in quadrant cells
   - Table: Migration Status by System - **badges are clickable**
3. **Charts Row** (2 columns)
   - SOLO → ACME doughnut chart
   - Work Distribution by Tech Lead bar chart
4. **Tables**
   - At Risk for 2/27/26
   - Future Migrations (no deadline)
   - Obsolete Apps (reference)
   - Deactivated Apps (reference)

### Interactive Elements

**Clickable Numbers (Overview card):**
- Active Apps → modal showing all 29 apps with status
- At Risk → modal showing 6 at-risk apps
- Obsolete → modal showing 12 obsolete apps

**Clickable Badges (System table):**
- "Off SOLO" badges → modal showing Done apps (green) and Remaining apps (amber)
- "Off Sentry 1" badges → modal showing Done apps (green) and Remaining apps (amber)

**Quadrant Bubble Tooltips:**
- Hover over any system bubble to see:
  - ✓ = Fully complete (100%)
  - ◐ = Partially complete (1-99%)
  - ○ = Not started (0%)
  - — = N/A (not applicable)

### Color Scheme

```python
COLORS = {
    'done': '#059669',          # Green (emerald)
    'to_do': '#f59e0b',         # Amber
    'in_progress': '#3b82f6',   # Blue
    'obsolete': '#64748b',      # Slate gray
    'na': '#94a3b8',            # Light slate
    'at_risk': '#ea580c',       # Orange
    'primary': '#1e40af',       # Deep blue
    'secondary': '#475569'      # Dark slate
}
```

### Print CSS
The dashboard includes `@media print` styles for clean PDF export:
- Removes shadows, hover effects, modals
- Preserves all colors and backgrounds
- Handles page breaks properly

---

## Recent Session Changes (Feb 17, 2026)

### Session 3: Versioning System & Quadrant Fixes

**Major Changes:**

1. **BzBee Quadrant Bug Fixed**
   - BzBee was incorrectly placed in "Debut Sentry" middle row (y=50)
   - Root cause: Code treated ANY partial Sentry progress as "Debut Sentry"
   - Fix: Systems stay in Sentry 1.0 row until 100% off Sentry 1.0
   - BzBee now correctly at y=83 (upper right quadrant)

2. **Target Auth System Logic Added**
   - Tracks which auth system apps migrate TO (Debut-Sentry vs Sentry 2.0)
   - When VPP completes migration → middle row (ACME + Debut Sentry)
   - When other systems complete → bottom row (ACME + Sentry 2.0)

3. **Versioning System Implemented**
   - Format: `vX.Y` where X = major (dashboard changes), Y = minor (data updates)
   - Current version: v2.1
   - Version displayed in header: `v2.1 • Last Updated: February 17, 2026`
   - Auto-increments minor version when data file hash changes
   - Major version set in script: `DASHBOARD_MAJOR_VERSION = 2` (line 55)

4. **Auto-Detect Excel File**
   - Script now finds most recent `.xlsx` in `data/input/`
   - No need to use specific filename
   - User can add date suffix (e.g., `_021726`) for tracking

5. **New Files Created**
   - `data/version_state.json` - tracks version and data file hash
   - `CHANGELOG.md` - auto-updated with each version change

**Files Modified:**
- `scripts/generate_dashboard.py` - versioning, auto-detect, quadrant fixes

---

## Previous Session Changes (Feb 10, 2026)

### Session 2: Complete Data Logic Overhaul

**Major Changes:**

1. **Column G & I Added**
   - Now reads Column G (Direct Integration)
   - Now reads Column I (Auth Sys Status) as cross-check
   - Direct Integration counts toward "Off Sentry 1.0"

2. **Status Terminology Changed**
   - OLD: "Completed", "Not Started", "Blocked", "Not Needed"
   - NEW: "Done", "To Do", "In Progress", "Obsolete"
   - Removed "Blocked" entirely (not in Excel Column L)

3. **Obsolete Apps Separated**
   - Obsolete apps now completely excluded from all stats
   - Shown only in reference table at bottom
   - System totals exclude obsolete apps

4. **System Matrix Rewritten**
   - Now tracks two INDEPENDENT migration tracks
   - OFF SOLO = apps on ACME
   - OFF SENTRY 1 = apps on Sentry 2.0/Direct Int/Debut-Sentry
   - Fixed logic to count correctly

5. **Notes Column Removed**
   - Column Q (Notes) no longer affects dashboard
   - Not displayed in any tables or modals
   - User can still use it in Excel for reference

6. **UI Enhancements**
   - Overview card: Removed legend, made all 3 numbers clickable with modals
   - System table: Made all badges clickable showing remaining/done apps
   - Quadrant chart: Fixed bubble positioning inside cells (not at edges)
   - Quadrant tooltips: Fixed to show real percentages (not display positions)

7. **Layout Reordered**
   - Moved System Migration Quadrant above the charts row
   - Better visual hierarchy

---

## Known Issues / Limitations

1. **PDF Generation:** Chrome headless blocked by Cursor sandbox
   - **Workaround:** Use browser print (Cmd+P → Save as PDF)
   - OR run Chrome headless command directly in Terminal.app

2. **Excel File Must Be Closed:** Script cannot read if Excel has the file open

3. **Environment Detection:** Environment (INT/PRD/STG/QAT) parsed from app name suffix

---

## System Names

- **BzBee** (4 apps)
- **FGS** (3 apps)
- **GSS** (9 apps)
- **Genie** (6 apps)
- **TM** (3 apps)
- **VPP** (3 apps)
- **Workforce** (1 app)

---

## Tech Stack

- **Python 3** (dashboard generation)
- **Chart.js** (charts in HTML)
- **Custom XML parser** (reads strict OOXML Excel format)
- **No external dependencies** required (uses built-in Python libraries)

---

## To Create PDF (Two Options)

**Option 1: Browser Print (Easiest)**
```
1. Open dashboard in Chrome/Safari
2. Press Cmd + P
3. Destination → "Save as PDF"
4. Layout → Landscape
5. Save
```

**Option 2: Chrome Headless (Terminal)**
```bash
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --no-sandbox \
  --print-to-pdf="/Users/sam.levine.-nd/Desktop/2026 Projects/MyID_Migration/reports/MyID_Migration_Dashboard.pdf" \
  --print-to-pdf-no-header --window-size=1400,1200 \
  "file:///Users/sam.levine.-nd/Desktop/2026 Projects/MyID_Migration/reports/MyID_Migration_Dashboard.html"
```

---

## Important Notes for Next AI Agent

1. **Status values are strict:** Only use Done/In Progress/To Do/Obsolete
2. **Two independent tracks:** SOLO→ACME and Sentry 1.0→Off are tracked separately
3. **Column G matters:** Direct Integration counts as "Off Sentry 1.0"
4. **Obsolete = excluded:** Never include obsolete apps in stats/totals
5. **Notes column = display only:** Never use Column Q to drive dashboard logic
6. **Tooltips use real percentages:** Bubble x/y are display positions, off_solo_pct/off_sentry1_pct are real data
7. **Quadrant Y-positioning:** Systems stay in Sentry 1.0 row until 100% complete
8. **Target auth system:** VPP targets Debut-Sentry (middle row), others target Sentry 2.0 (bottom row)
9. **Versioning:** Auto-increments on data change; major version is manual (line 55 in script)
10. **Excel auto-detect:** Script finds newest .xlsx in data/input/ - no hardcoded filename

---

## Files to Never Modify

- Excel file column structure (don't add/remove/reorder columns)
- Color scheme (approved by user)
- Status terminology (Done/To Do/In Progress/Obsolete)

---

## Questions to Ask User If Unclear

1. New column added to Excel? Confirm column letter mapping.
2. New status value appears? Confirm how to categorize it.
3. Change to obsolete logic? Confirm inclusion/exclusion rules.
4. UI/layout change? Confirm visual design expectations.

---

**End of Context File**

For full transcript from this session, see:  
`/Users/sam.levine.-nd/.cursor/projects/.../agent-transcripts/[session-id].txt`
