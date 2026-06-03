# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v1.2.0] - 2026-06-04

### Added
- **Secondary data infrastructure** — a multi-source fallback that resolves prices when Yahoo Finance is unresponsive or returns gaps. yfinance remains the primary source; only the symbols it cannot price are handed off. Per exchange, live-first with an EOD bhavcopy backstop:
  - **NSE**: live via NseKit (`cm_live_equity_full_info`), EOD via jugaad-data bhavcopy
  - **BSE**: live via `bse` (`quote`), EOD via `bse` bhavcopy
- A symbol classifier that honours the existing portfolio convention (no dot → NSE `.NS`; `.BO` → BSE) and adapts it to each source's required naming — the `Summary Report.xlsx` format is unchanged.
- **Curated terminal log** for the data pipeline — colored, sectioned console output (primary attempt, per-exchange routing, per-source resolution, boxed resolution summary) for both the dashboard price fetch and analysis history fetch.
- **Themed progress card** (gold accent, matching the design system) shown during data loads in both Dashboard and Analysis modes; re-armed on "Refresh Prices".

### Changed
- **Renamed the application from SWING to SAMHITA (संहिता).** The entry point is now `samhita.py` (run with `streamlit run samhita.py`); the portfolio data format (`Summary Report.xlsx`) and all behavior are unchanged.
- All native Streamlit cache spinners silenced; fetch diagnostics now route to the terminal log so the UI surface stays cohesive.
- **Unified vertical rhythm** across the layout — a single scale-based system: base 16px, binding tier 28px (header→content, tabs→content), major separation 40px (hero, section→section, KPI→tabs). The base flow gap is pinned to the token scale rather than relying on Streamlit's implicit default.
- Removed the redundant "Portfolio Snapshot" section header so the KPI row sits directly below the masthead.

### Fixed
- Eliminated a stray floating divider under the tab strip (a duplicate of the tab underline drawn by both CSS and baseweb's native track) and closed the empty gap its removal left.
- Collapsed phantom vertical gaps left by emptied progress-card placeholders.
- De-duplicated the terminal resolution summary on Streamlit's first-load double-run.
- Suppressed noisy upstream warnings in the curated log: yfinance `auto_adjust` `FutureWarning` (now explicit on all downloads) and pandas `pct_change` `fill_method` `FutureWarning`.

### Dependencies
- Added `NseKit`, `jugaad-data>=0.33.1`, and `bse` for the secondary data sources.

---

## [v1.1.1] - 2026-04-05

### Changed
- Modernized import organization for better readability and maintainability
- Added comprehensive type hints to all public functions for improved IDE support
- Enhanced function documentation with clear docstrings

### Fixed
- Corrected installation command in README.md (`streamlit run swing.py` instead of `app.py`)
- Removed unused `base64` import from main entry point

### Removed
- Eliminated dead code and unreachable execution paths
- Cleaned up redundant variable assignments and commented-out legacy code

### Security
- Ensured all data fetching functions have proper error handling and fallback values
- Validated production-ready configuration for client deployment

---

## [v1.1.0] - Previous Release

Institutional-grade analytics, benchmark comparison, advanced metrics
