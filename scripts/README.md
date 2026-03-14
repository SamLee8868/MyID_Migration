# MyID Migration Scripts

This folder contains automation scripts for generating the migration tracking dashboard and reports.

## Available Scripts

### 1. `generate_dashboard.py`
**Purpose:** Generates interactive HTML dashboards from the CSV tracker data

**Usage:**
```bash
python3 scripts/generate_dashboard.py
```

**Output:**
- `reports/MyID_Migration_Dashboard.html` - Interactive dashboard with clickable cards
- `reports/MyID_Migration_Report_Print.html` - Print-optimized report

**When to run:** After every update to `data/input/MyID_Migration_Tracker.csv`

---

### 2. `generate_pdf.sh`
**Purpose:** Converts the print-optimized HTML report to a shareable PDF

**Usage:**
```bash
bash scripts/generate_pdf.sh
```

**Output:**
- `reports/MyID_Migration_Report.pdf` - PDF version of the status report

**Requirements:** Google Chrome (already installed on your system)

**When to use:** When you need a PDF 1-pager to share with the team via email, Slack, or presentation

---

### 3. `generate_pdf.py`
**Purpose:** Alternative Python-based PDF generator (requires manual browser step)

**Note:** Use `generate_pdf.sh` instead - it's simpler and fully automated

---

## Quick Workflow

1. **Update the data:**
   ```bash
   # Edit the CSV file in Excel or text editor
   open data/input/MyID_Migration_Tracker.csv
   ```

2. **Generate dashboards:**
   ```bash
   python3 scripts/generate_dashboard.py
   ```

3. **Generate PDF (optional):**
   ```bash
   bash scripts/generate_pdf.sh
   ```

4. **View/Share:**
   - Open `reports/MyID_Migration_Dashboard.html` in browser for interactive view
   - Share `reports/MyID_Migration_Report.pdf` with team

---

## Troubleshooting

### Python command not found
Use `python3` instead of `python`:
```bash
python3 scripts/generate_dashboard.py
```

### PDF generation fails
If the shell script doesn't work, you can manually print to PDF:
1. Open `reports/MyID_Migration_Report_Print.html` in any browser
2. Press Cmd+P (File → Print)
3. Select "Save as PDF" from the PDF dropdown
4. Save to `reports/MyID_Migration_Report.pdf`

### CSV encoding issues
Make sure the CSV is saved as UTF-8 format. In Excel:
- File → Save As → Format: CSV UTF-8 (Comma delimited)
