# MyID Migration Dashboard

**[Repo](https://github.com/SamLee8868/MyID_Migration)** · A **migration tracking dashboard** that turns an Excel or CSV tracker into a visual, interactive HTML report. Tracks two parallel migrations: **SOLO → ACME** (identity) and **Sentry 1.0 → Off Sentry 1.0** (Sentry 2.0, Direct Integration, or Debut-Sentry).

**Audience:** Directors, Sr. Managers, Tech Leads, Dev Leads, PMs/SMs

---

## Demo / Showcase (This Repo)

This repo includes **dummy data** so you can run and show the dashboard without internal data.

```bash
git clone <your-repo-url>
cd MyID_Migration
python3 scripts/generate_dashboard.py
open reports/MyID_Migration_Dashboard.html
```

- **Data:** `data/input/Demo_MyID_Migration_Tracker.csv` (sanitized demo data)
- **No Excel required** — the script uses the demo CSV when no `.xlsx` is present
- **Versioning** — dashboard version auto-increments when the data file changes (see `CHANGELOG.md`)

To use your **own data**: add an Excel file (`.xlsx`) to `data/input/`; the script will use the most recent one and ignore the CSV.

---

## Quick Start

```bash
cd MyID_Migration
python3 scripts/generate_dashboard.py
open reports/MyID_Migration_Dashboard.html
```

**No dependencies required** for the main script — it uses only Python standard library (Excel is parsed via zip + XML). Optional: `openpyxl` for older Excel formats.

---

## How to Update the Dashboard

### Option A: Excel (primary in production)

1. Download or export your tracker as `.xlsx` and save to `data/input/` (e.g. `Tracker_MMDDYY.xlsx`).
2. Close the file if it’s open in Excel.
3. Run:
   ```bash
   python3 scripts/generate_dashboard.py
   ```
4. Open or refresh `reports/MyID_Migration_Dashboard.html`.

### Option B: CSV (demo or fallback)

1. Edit `data/input/Demo_MyID_Migration_Tracker.csv` (or add any `.csv` in `data/input/`).
2. Run the script as above. With no Excel present, the script uses the demo CSV (or the latest CSV in `data/input/`).

---

## File Structure

```
MyID_Migration/
├── data/input/
│   └── Demo_MyID_Migration_Tracker.csv   ← Demo data (committed)
│   └── *.xlsx                            ← Your Excel (gitignored)
├── data/version_state.json               ← Version state (gitignored)
├── reports/
│   └── MyID_Migration_Dashboard.html     ← Generated dashboard
├── scripts/
│   └── generate_dashboard.py             ← Dashboard generator
├── docs/
│   ├── PROJECT_CONTEXT.md                ← Full project context
│   └── PROJECT_ANALYSIS.md               ← Technical analysis (exec summary, interview, resume)
├── CHANGELOG.md                          ← Version history
└── README.md                             ← You are here
```

---

## CSV Columns (for demo or fallback)

| Column | Valid Values | Notes |
|--------|---------------|-------|
| Platform/App | Text | App or environment name |
| Environment | INT, PRD, STG, QAT | Optional |
| System | BzBee, FGS, GSS, Genie, TM, VPP, Workforce | |
| Owner / Tech Lead | Text | |
| Current Auth System | Sentry 2.0, Sentry 1.0, SOLO, Direct Integration, N/A | Used for quadrant |
| ACME Migration Status | Done, Completed, In Progress, To Do, Not Started, Blocked, Obsolete, Not Needed | |
| Sentry Migration Status | Completed, Not Started, In Progress, N/A | “Completed” = off Sentry 1.0 |
| ACME Target Deadline | e.g. 2/27/26, Future | |
| At Risk for 2/27/26 | Yes, No | |
| JIRA Ticket | Text | e.g. DEMO-101 |

---

## Versioning

- **vX.0** — Major (dashboard/UI changes; set in script).
- **vX.Y** — Minor (auto-increments when the data file content changes).
- Version appears in the dashboard header and in `CHANGELOG.md`.

---

## Creating a PDF

1. Open `reports/MyID_Migration_Dashboard.html` in a browser.
2. **Cmd + P** (or Ctrl + P) → **Save as PDF**.
3. Use **Landscape** for best layout.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| “No data file found” | Ensure `data/input/` contains a `.csv` or `.xlsx` file. |
| Dashboard shows old data | Re-run the script after saving your Excel/CSV. |
| Excel “in use” or locked | Close the workbook in Excel before running the script. |

---

## License & Use

Use this repo as a portfolio piece or internal template. Replace dummy data with your own for real use.
