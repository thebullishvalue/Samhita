# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [v2.0.9] - 2026-11-14
### Fixed
- **One button face across the family.** Measured in all eight apps, in Paper and Slate, at rest
  and on hover, the primary (run) button had drifted into several faces: a grey rim on the accent
  fill and a light-grey hover with dark type (Paper's generic button rules outranked the primary's
  own), a dark label on the accent (a Paper rule inking every markdown paragraph reached the
  button's label — Sanket's Run Screener), and Streamlit's own sans at 8px corners (Pragyam). The
  generic rules no longer match the primary at all, and one face is stated once: accent fill and
  rim, white mono label, uppercase, 6px corners, each appearance's own darker accent on hover.
- **One segmented control.** The appearance switch's idle segments are unfilled with tertiary ink
  in every app (one filled them grey, one white, with three different label inks).

## [v2.0.8] - 2026-11-14
### Fixed
- **A panel's opening copy keeps its gap below the header's rule.** The header is markdown, and
  Streamlit's -16px bottom margin pulled the copy up under the rule: its first line sat 2px below
  the line. When text follows a header, the header keeps its full height, so the copy starts 18px
  below the rule, as in Arthagati's one-block panels. Charts and tables, which carry their own
  top inset, are unchanged.
- A toast's icon takes the accent (it kept the native near-white on Paper).
- *Return distribution:* the μ and VaR labels lean apart; centred, they collided whenever the
  two values were close (measured on a tablet).

## [v2.0.7] - 2026-11-14
### Fixed
- **A fidelity pass over every page.** Every page, tab and expander was scanned at 1440, 1024, 834
  and 390px in Paper and Slate for clipped or overlapping text, content past its panel or the
  page, chart-label collisions, native-theme colours on Paper and unreadable contrast; each
  defect was fixed at the rule that caused it.
  - *Panel header rows wrap.* On a phone a header's control (the 3M…ALL window strip) was pushed
    wholly outside its panel, invisible and untappable; it now drops to its own line.
  - *Nothing in the rail is cut with an ellipsis.* Page names on the 200px tablet rail, the
    tagline, and a select's value wrap instead.
  - *The page no longer drags sideways.* A KPI card's hidden tooltip opened to the right of an
    icon in the card's top-right corner and widened the page by 171px; it opens over its card.
  - *No native near-white or near-black on Paper.* The open-rail chevron (the only way to the
    navigation on a phone or tablet), help marks, slider min/max labels, expander rows and
    borders, toasts and unstyled widget labels are painted from tokens.
  - *Fields share one height.* A text input's wrapper kept a transparent 1px border, so every
    text field was 2px taller than the select or number field beside it.
  - *The instrument chip* no longer clips the tops of its capitals.
  - *Charts:* reference-line labels (Max drawdown, Target, Market, 50%, 80%) sit inside the plot
    instead of past its edge; value labels get room on narrow screens; the gain waterfall's names
    are vertical (every other one on a tablet or phone); the monthly heatmap's values hide on a
    phone (tap readout); the contribution chart's subplot titles fit half a phone.

## [v2.0.6] - 2026-11-13
### Fixed
- **Nothing sits on a panel's edge.**
  - *Charts.* The chart box's 8px padding only displaced the figure, because Streamlit fixes that box
    at the figure's height: 8px out of its bottom (onto a footer's rule, or under the panel's
    clipping edge: the x labels, a bottom legend) and, on phones, 16px past the panel's right edge
    (the last x tick read "10(", the legend's end was cut). The top and bottom inset is now padding
    on the chart's container, and the figure fits inside it; the side inset is the figure's own
    margins (`PLOTLY_MARGIN` l/r +8).
  - *A panel's last line.* Streamlit gives every markdown block a -16px bottom margin, so a panel
    that clips at `overflow: hidden` ended 16px before its body did. Body markdown inside a panel
    keeps a zero margin, so a wrapped last line is no longer cut on a phone.
  - *Panel headers.* A long context line (instrument · window · units) wraps at word breaks instead
    of running off the panel on a phone.

## [v2.0.5] - 2026-11-13

### Fixed
- **The chosen day reads as one disc.** The previous fix filled the day's inner box while BaseWeb
  still drew its own selection ring around it (a square inside a circle). The fill now goes on that
  ring (the cell's `::after`) and the inner box stays clear: one accent disc with a white number,
  in both appearances.

## [v2.0.4] - 2026-11-13

### Fixed
- **The date picker's chosen day had no fill.** This BaseWeb build marks the chosen day with
  `aria-label="Selected. …"`, not `aria-selected`, so the calendar block's reinstatement never
  matched and its transparent reset wiped the fill. The chosen day is filled from the accent again,
  in both appearances.

## [v2.0.3] - 2026-11-10

### Fixed
- **Black bands on phones in dark mode.** With both `[theme.light]` and `[theme.dark]` in
  `.streamlit/config.toml`, Streamlit's native widgets followed the viewer's OS while the app
  follows its Paper/Slate toggle: on a dark-mode phone in Paper, the date picker's empty cells
  and the tab strip's overflow fade were painted near-black. The config now has exactly one
  `[theme]` section (a fixed native layer for every viewer, as in Pragyam), the calendar is
  painted from the app's own tokens in both appearances (Pragyam's calendar block), and the
  tab-strip fade uses the page background token.

## [v2.0.2] - 2026-11-10

### Changed
- **Tattva's tab icon.** The browser-tab icon is Tattva's exact mark (its cobalt
  ring-and-line, `#3D6FE8`, in Tattva's own base64 encoding), as in Nishkarsh, Nivesa and Swing,
  so the apps' tabs match. It was the same mark in a lighter blue (`#4C7DF0`).

## [v2.0.1] - 2026-11-10

### Fixed
- **iPad portrait: a blank strip when the sidebar is collapsed.** At 1024px and below the
  narrow-rail floor (200px) also held the collapsed sidebar's slot in the layout; it now applies
  only while the sidebar is open.
- **Rows of columns stopped 16px short** of the panels around them (KPI strips, card rows):
  Streamlit's column basis relies on flex-grow, which the design system turns off; each unwrapped
  row now gets the exact basis for its column count.
- **Tables lost their bottom 8px**: the gap under the panel header was a margin on the table's
  iframe that its container did not account for; it is now container padding the iframe height
  includes.
- **Tables lost their last row**: cell padding rendered ~30px rows against the 27px budget the
  iframe is sized by; padding now derives from the row height.
- Same fixes as Tattva 2.8.1, Nishkarsh 2.5.2–2.5.3 and Nivesa 3.0.1.

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
