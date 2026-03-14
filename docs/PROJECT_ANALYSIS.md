# MyID Migration Dashboard — Project Analysis

*Generated from codebase and config only. No invented details.*

---

## 1. WHAT IT DOES (Executive Summary)

This project is a **migration tracking dashboard** that turns a single Excel tracker (maintained on SharePoint) into a visual, interactive HTML report. It tracks two company-wide migrations: moving applications from SOLO to ACME authentication (MyID), and from Sentry 1.0 to Sentry 2.0 (or Direct Integration / Debut-Sentry). The dashboard shows how many applications are done, in progress, or at risk by system and tech lead, with a quadrant chart, KPI cards, and clickable modals. Directors, senior managers, tech leads, and PMs use it to see migration status at a glance and to export a clean PDF for status updates. Data is updated by downloading the latest Excel from SharePoint, saving it into the project folder, and re-running one Python command; the dashboard version number auto-increments when the data file changes.

---

## 2. EXPLAIN IT LIKE I'M 5

Imagine you have a **big list on a whiteboard** (the Excel file) where people write which apps have moved to the new front door (ACME) and which have moved to the new mailbox (Sentry 2.0). The list is messy and hard to read in meetings.

This project is like a **robot that reads that list** and draws a **pretty picture** (the dashboard): colored boxes that say “10 done, 19 to do,” a **bubble map** showing which teams are ahead or behind, and **clickable labels** so when you tap a number you see the actual app names. The robot only needs you to **put the newest list in a special folder** and say “go”; it figures out which file is newest, checks if the list changed, and if so it bumps the version number and writes a line in a **changelog** so everyone knows what changed.

**Tools:**  
- **Python** is the robot that reads the list and draws the picture.  
- **Excel (xlsx)** is the list; the robot opens it like a zip and reads the XML inside so it works even when Excel uses strict formats.  
- **HTML + Chart.js** is the picture: one file that runs in the browser with doughnut charts, bar charts, and a bubble chart, no server needed.  
- **JSON and Markdown** are the robot’s memory: it stores the current version and a hash of the list so it knows when to bump the version and what to write in the changelog.

---

## 3. FULL TECHNICAL BREAKDOWN

### a) Tech stack

| Layer | Technology |
|-------|------------|
| **Language** | Python 3 (stdlib + optional openpyxl; v3 Excel uses built-in zip + xml.etree only) |
| **Data source** | Excel (.xlsx) — OOXML parsed via zipfile + ElementTree; fallback: CSV |
| **Output** | Single-file HTML (inline CSS + JS) |
| **Charts** | Chart.js (loaded from cdn.jsdelivr.net) |
| **State** | JSON (`data/version_state.json`), Markdown (`CHANGELOG.md`) |
| **Deployment** | None — static HTML; run script locally, open file in browser or print to PDF |

### b) What each major file or folder does

| Path | Purpose |
|------|---------|
| `scripts/generate_dashboard.py` | Main entry: finds latest Excel, parses it, computes stats and system matrix, applies versioning, emits HTML with embedded data and Chart.js config. |
| `data/input/` | Holds Excel (and optional CSV). Script picks the **newest .xlsx** by mtime; filenames often include date suffix (e.g. `_022726`). |
| `data/version_state.json` | Persists major/minor version, last data file hash, and last filename; used to decide when to bump minor version and update changelog. |
| `reports/MyID_Migration_Dashboard.html` | Generated dashboard; do not edit by hand. |
| `CHANGELOG.md` | Human-readable version history; script appends entries when data or major version changes. |
| `docs/PROJECT_CONTEXT.md` | Canonical project context for handoff and AI agents (workflow, column mapping, logic rules). |
| `README.md` | User-facing quick start, update steps, column reference, troubleshooting, PDF instructions. |
| `docs/PROJECT_ANALYSIS.md` | This document. |
| `.cursor/rules/*.mdc` | Cursor/IDE rules (ask questions, no assumptions, context preservation, etc.). |
| `archive/` | Backups / older artifacts. |

### c) End-to-end data flow

1. **Input:** User places an Excel file in `data/input/` (e.g. downloaded from SharePoint with a date suffix).
2. **Discovery:** Script lists `*.xlsx` in `data/input/`, sorts by modification time, uses the newest.
3. **Parse:** Excel is opened as a zip; `xl/sharedStrings.xml` and `xl/worksheets/sheet1.xml` are read and parsed with ElementTree. Rows are mapped to columns A–Q; v3 format is detected by “System” in row 1 column B.
4. **Normalize:** Each row becomes an app record (platform, system, POC, obsolete, Sentry 1.0/2.0/Direct/Debut flags, SOLO/ACME, migration status, due date, JIRA, etc.). Obsolete and “not in use” apps are filtered; statuses are normalized (e.g. “Completed” → “Done”).
5. **Compute:** Stats (ACME done/to do/at risk, Sentry done/in progress/to do/N/A), system matrix (per-system off-SOLO and off–Sentry 1.0 counts and percentages, target auth for quadrant), and tech-lead workload.
6. **Version:** Hash of the chosen Excel file is compared to `version_state.json`. If different (or if major version was bumped in script), minor version increments, state and `CHANGELOG.md` are updated.
7. **Output:** One HTML file is written to `reports/` with inline CSS/JS, JSON blobs for modals and quadrant data, and Chart.js config for doughnut, bar, and bubble charts.

No server, no database, no API calls at runtime.

### d) APIs or external services

- **Chart.js:** Loaded from `https://cdn.jsdelivr.net/npm/chart.js` in the generated HTML. No other external requests.
- **SharePoint:** Not accessed by the app. User downloads the Excel manually; the script only reads the local file.

### e) Authentication and security

- No auth in the app. The HTML is static; opening it is equivalent to opening any local HTML file.
- No secrets in the repo; data is the Excel/CSV the user places in `data/input/`.
- Version state and changelog live under the project directory and are only used by the script.

### f) Deployment and run

- **Run:** From project root: `python3 scripts/generate_dashboard.py`. Then open `reports/MyID_Migration_Dashboard.html` in a browser (or print to PDF).
- **Deployment:** There is no deployed service. The “deployment” is generating the HTML and optionally saving it to a shared location or emailing the PDF.

### g) Technically complex or interesting parts

- **Excel without openpyxl for v3:** The script parses OOXML by unzipping the xlsx and parsing `sharedStrings.xml` and `sheet1.xml` with ElementTree, including namespace normalization for strict OOXML. This avoids dependency on openpyxl for the primary format.
- **Quadrant positioning logic:** Systems are placed in a 2×3 grid (SOLO vs ACME × Sentry 1.0 / Debut-Sentry / Sentry 2.0). Logic distinguishes “still has Sentry 1.0 work” (top row) from “100% off Sentry 1.0” and then, among the latter, “target is Debut-Sentry” (middle) vs “target is Sentry 2.0” (bottom). BzBee-style bugs (partial progress incorrectly in Debut row) were fixed by tying row to completion and target auth.
- **Versioning:** Minor version auto-increments only when the data file’s hash changes; major is manual (constant in script). Changelog and state stay in sync with the generated dashboard version.

### h) Known limitations / shortcuts

- **Excel must be closed** when the script runs (or the file is not writable / read consistently on some setups).
- **No direct SharePoint integration** — user must download and save the file; script does not fetch from the link.
- **Single HTML file** — all data is embedded; large datasets could make the file big.
- **PDF:** Print-to-PDF works from the browser; Chrome headless is documented but may be blocked in sandboxed environments (e.g. Cursor).
- **CSV fallback** exists but the primary path is Excel; CSV column set may not match the full v3 column mapping.

---

## 4. HOW TO TALK ABOUT IT IN AN INTERVIEW

### 30-second elevator pitch

“I built an internal migration tracking dashboard that turns our SharePoint Excel tracker into a single-page HTML report with KPIs, charts, and a quadrant view. A Python script parses the Excel file—using raw OOXML parsing so we’re not tied to a specific library—computes stats and system-level progress, and emits self-contained HTML with Chart.js. We added automatic versioning so the report version bumps whenever the data file changes, and we track that in a changelog. Stakeholders get a one-command refresh and a clear view of what’s done, in progress, and at risk for two parallel migrations.”

### 2-minute deep-dive

“We have two company-wide migrations—SOLO to ACME for identity and Sentry 1.0 to Sentry 2.0 or alternatives—and the source of truth is an Excel matrix on SharePoint. I wanted to avoid manual copy-paste and give directors and tech leads a single place to see status.

“The pipeline is: drop the latest Excel into a folder, run one Python script. The script finds the newest xlsx by modification time—we use date suffixes on the filename—and parses it without openpyxl by unzipping the xlsx and parsing the sheet and shared-strings XML. That lets us support the strict OOXML format our SharePoint export uses. We normalize statuses, filter obsolete and deactivated rows, then compute two tracks: ACME (off SOLO) and Sentry (off Sentry 1.0), including per-system percentages and target auth (Debut-Sentry vs Sentry 2.0) for the quadrant.

“We also added versioning: we hash the data file and store state in JSON. If the hash changes, we bump the minor version and append to a Markdown changelog. Major version is a constant in the script for dashboard-only changes. The output is one HTML file with inline CSS and JS and Chart.js from a CDN—doughnut, bar, and bubble charts—and JSON embedded for modals and quadrant data. So there’s no backend; it’s static and easy to share or print to PDF.

“One non-trivial piece was the quadrant logic: we had to fix systems with partial Sentry progress being placed in the wrong row. Now placement is based on whether the system is fully off Sentry 1.0 and, if so, whether their target is Debut-Sentry or Sentry 2.0.”

### 3 likely interview questions and strong answers

**Q1: How do you handle the Excel file when your team doesn’t control the format?**  
We don’t assume a specific library. For the v3 format we parse the xlsx as a zip and read the OOXML XML (sheet and shared strings) with the standard library. We detect format by checking a header cell and then map columns by letter. That way we’re resilient to strict OOXML and don’t depend on openpyxl for the main path. We still have a CSV fallback and document the column mapping so changes can be accommodated.

**Q2: How would you scale this if the number of applications grew a lot?**  
Right now all data is embedded in one HTML file, which is fine for tens of apps. If we scaled to hundreds or thousands, I’d split data from presentation: e.g. the script writes a JSON file and the HTML fetches it, or we’d move to a small backend that serves the JSON and the HTML is a static front end. We could also paginate or filter the tables and modals and only load visible segments. Versioning and hashing would still apply to the source Excel or to the generated JSON.

**Q3: Why auto-increment version on data change instead of on every run?**  
We want the version to reflect “something changed that stakeholders care about.” If you re-run without changing the file, the report is identical, so the version shouldn’t change. We hash the data file and only bump the minor version when the hash changes, and we append to the changelog only then. That keeps the changelog meaningful and avoids noise like “v2.47” with no real changes.

---

## 5. RESUME BULLET POINTS

**Implementation & technical**

- Built a Python pipeline that parses Excel (OOXML) via zip and XML to generate a static HTML migration dashboard, avoiding external Excel libraries for the primary format.
- Implemented automatic versioning (major/minor) and changelog updates using file hashing and JSON state so report versions reflect actual data or dashboard changes.
- Designed quadrant chart logic to map 7 systems onto a 2×3 grid (SOLO/ACME × Sentry 1.0 / Debut-Sentry / Sentry 2.0) with correct placement for partial vs complete migration and target auth (Debut vs Sentry 2.0).
- Integrated Chart.js (doughnut, bar, bubble) into a single-file HTML dashboard with embedded JSON and print-optimized CSS for PDF export.
- Added automatic selection of the latest Excel file by modification time so stakeholders can drop date-stamped downloads into a folder and re-run one command to refresh the report.

**Process & collaboration**

- Documented project context, column mapping, and versioning rules in `PROJECT_CONTEXT.md` to support handoff and AI-assisted maintenance.
- Delivered a one-command workflow (download Excel → run script → open HTML) for directors, tech leads, and PMs to view SOLO→ACME and Sentry 1.0→2.0 migration status.
- Reduced manual steps in status reporting by generating a shareable HTML/PDF dashboard from the canonical SharePoint Excel tracker. *[Confirm with stakeholder: e.g. “reduced status prep time by X minutes per cycle.”]*

**Outcomes** *(fill in numbers where you have them)*

- Tracked migration status for 29 active applications across 7 systems with at-risk visibility against a 2/27/26 deadline. *[Optional: “surfaced X at-risk items in time for remediation.”]*
- Enabled versioned changelog and data-driven version bumps so each report refresh is traceable to a specific data file and date. *[Optional: “reduced confusion over which report was latest.”]*

**Fill-in / confirm**

- “Saved X hours per sprint (or per month) on status report preparation” — confirm with actual usage.
- “Reduced errors from manual copy-paste by automating report generation from the single source Excel” — confirm if there was a prior manual process.
- “Improved visibility for X stakeholders (directors, tech leads, PMs)” — replace X with approximate number if known.
