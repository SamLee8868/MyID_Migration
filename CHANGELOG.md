# MyID Migration Dashboard Changelog

This file tracks all version changes to the dashboard.
- **Major versions (x.0):** Dashboard UI/logic changes
- **Minor versions (#.x):** Data file updates

---

## v2.2 - March 14, 2026
- Data file: `Demo_MyID_Migration_Tracker.csv`
- Stats: 14 ACME Done, 13 To Do, 9 At Risk

## v2.1 - March 14, 2026
- Data file: `MP&A - Okta-Based MyID Migration (SOLO to ACME)_022726.xlsx`
- Stats: 13 ACME Done, 16 To Do, 3 At Risk

## v2.2 - February 27, 2026
- Data file: `MP&A - Okta-Based MyID Migration (SOLO to ACME)_022726.xlsx`
- Stats: 13 ACME Done, 16 To Do, 3 At Risk

## v2.1 - February 17, 2026
- Data file: `MP&A - Okta-Based MyID Migration (SOLO to ACME)_021726.xlsx`
- Stats: 10 ACME Done, 19 To Do, 6 At Risk
- Added versioning system with auto-increment on data changes
- Script now auto-detects most recent Excel file in `data/input/`## v2.0 - February 17, 2026
- **Dashboard Change:** Fixed BzBee quadrant positioning bug
  - BzBee was incorrectly placed in "Debut Sentry" middle row
  - Now correctly stays in "Sentry 1.0" top row until migration is 100% complete
- **Dashboard Change:** Added target auth system logic
  - Systems targeting Debut-Sentry (like VPP) will land in middle row when complete
  - Systems targeting Sentry 2.0 will land in bottom row when complete
- Previous data from v1.x using older Excel format
