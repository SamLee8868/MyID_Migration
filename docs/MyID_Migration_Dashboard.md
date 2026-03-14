# MyID Migration Dashboard

**SOLO → ACME & Sentry 1.0 → Sentry 2.0 Migration Tracking**

*Last Updated: February 6, 2026*

---

## Summary at a Glance

### ACME Migration (SOLO → ACME)

| Status | Count |
|--------|-------|
| ✅ Completed | 13 |
| 🔵 Not Started | 18 |
| 🔴 Blocked | 3 |
| 🟡 Not Needed | 20 |
| **Total** | **54** |

### Sentry Migration (1.0 → 2.0)

| Status | Count |
|--------|-------|
| ✅ Complete / Not Needed | 30 |
| 🔵 Not Started | 3 |
| ⬜ N/A (SOLO Apps) | 21 |
| **Total** | **54** |

### Key Metrics

| Metric | Count |
|--------|-------|
| ⚠️ At Risk for 2/27/26 | 9 |
| 🔴 Currently Blocked | 3 |

---

## ⚠️ At Risk for 2/27/26 Deadline (9 apps)

**All items are assigned to Ricardo.**

| Platform/App | Environment | System | ACME Status | Sentry Status | JIRA |
|--------------|-------------|--------|-------------|---------------|------|
| mp-vpp-int | INT | VPP | Not Started | Not Started | PLAT-1879 |
| mp-vpp-stg | STG | VPP | Not Started | Not Started | PLAT-1879 |
| mp-vpp-prd | PRD | VPP | Not Started | Not Started | PLAT-1879 |
| sentry-vpp-int | INT | VPP | Not Started | N/A | - |
| sentry-vpp-stg | STG | VPP | Not Started | N/A | - |
| sentry-vpp-prd | PRD | VPP | Not Started | N/A | - |
| tm2-int | INT | TM | Not Started | Not Needed | - |
| tm2-stg | STG | TM | Not Started | Not Needed | - |
| tm2-prd | PRD | TM | Not Started | Not Needed | - |

---

## 🔴 Currently Blocked (3 apps)

| Platform/App | Environment | System | Owner | Blocker | JIRA |
|--------------|-------------|--------|-------|---------|------|
| fgs-saml-stg | STG | FGS | Jin Chung | Waiting on Jin, Mike, Bonnie, Koi (reached out 1/6) | APPS-2420 |
| fgs-prod-saml | PRD | FGS | Jin Chung | Waiting on Jin, Mike, Bonnie, Koi (reached out 1/6) | APPS-2420 |
| fgs-saml-int | INT | FGS | Jin Chung | Waiting on Jin, Mike, Bonnie, Koi (reached out 1/6) | APPS-2420 |

---

## Status Definitions

### ACME Migration Status
- **Completed** - Migration to ACME is done
- **Not Started** - Migration work has not begun
- **Blocked** - Cannot proceed due to dependency/issue
- **Not Needed** - App is disabled, doesn't exist, or doesn't require migration

### Sentry Migration Status
- **Not Started** - Currently on Sentry 1.0, needs upgrade to 2.0
- **Completed/Not Needed** - Already on Sentry 2.0
- **N/A** - App uses SOLO (not Sentry-based)

---

*Dashboard source: MP&A - Okta-Based MyID Migration (SOLO to ACME) Tracking*
