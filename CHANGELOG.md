# Changelog

All notable changes to **Samhita** are documented in this file.

The format is based on [Keep a Changelog 1.1.0](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html).

---

## [v2.0.21] - 2026-11-19
### Changed
- **The rail holds controls only.** The System readout under the controls is gone (version,
  "4-tier" sources and a "5 min" cache). Every member's rail reads identity, controls, appearance,
  and VAAYDO's never had one; where a readout stood, each app showed a different kind of fact, and
  each pushed the appearance switch further down. Nothing is lost: the version is in the footer.
- **The appearance switch sits at the foot on every screen.** Streamlit ends the rail with 96px of
  padding, so the switch "pinned to the foot" floated well above it on every screen, and on a rail
  taller than the screen it sat below the fold. The rail now ends 16px under the switch (plus a
  phone's home-bar inset), and the switch is pinned: where the rail scrolls, it stays at the foot
  on the rail's own ground and the controls pass behind it. A rail that carries the page list pins
  it on a desktop at least 820px tall; on a smaller screen it is the rail's last item, 16px from
  its end, so a long page list never leaves it half-hidden over the controls.

## [v2.0.20] - 2026-11-19
### Shared with the family
- The fidelity block of `ui/theme.css` carries the landing grids that Tattva, Nishkarsh, Nivesa,
  Pragyam, Sanket and VAAYDO now share with Arthagati (three equal-height system panels; four
  output cards, 4-up, 2-up, 1-up). Nothing on this app's pages changes.

## [v2.0.19] - 2026-11-18
### Changed
- **One console, shared by the family.** `logger_config.py` is now the family console, the same file
  in all nine apps, as the fidelity block of `theme.css` is for the page. Seven consoles had grown
  from one design (five copies of the same module, two more embedded in Samhita and Swing) and
  drifted: rules 60 and 70 wide, phases written three ways, timers rounded to whole seconds
  ("[0s]"), colour codes written into captured logs, a second run id printed under the first.
- **One grammar.** The product's banner once per process; a run's masthead (title, version, one
  run id, its start); its inputs in a labelled block; numbered phases with their time; numbered
  steps that close with what they produced and how long they took; labels in one column, long
  values wrapping under it at 72 columns; ✓ ⚠ ✗ ℹ in their colours; result cards; and a closing
  line, RUN COMPLETE or RUN FAILED, with the run's time and its warning and error counts.
- **Library output joins the run.** yfinance's HTTP errors (`HTTP Error 401: Unauthorized{"finance":
  …}`), its "possibly delisted" notices and Python warnings (a pandas RuntimeWarning with its full
  site-packages path) printed raw into the middle of a run. Each now arrives as one dimmed ⚠ line
  naming its source, once per run, counted as a warning.
- **Colour only on a terminal**, so a captured log is plain text (`NO_COLOR` / `FORCE_COLOR` honoured).
- Market data and analysis history are runs, and the four price tiers timed steps.

### Fixed
- **The Yahoo batch quote tier works again.** It called `yf.YfData`, which yfinance no longer
  exports at the top level, so it failed on every load ("module 'yfinance' has no attribute
  'YfData'") and prices fell through to batch history and the exchange bhavcopy. Prices resolve
  from the live quote in one call again (all 30 holdings in about half a second; it took 2.4s
  across three tiers).
- The NSE bhavcopy was read and logged twice per resolution (the previous-close repair read the
  file again); the two share one read.

## [v2.0.18] - 2026-11-18
### Fixed
- **Numbers written as text read as numbers.** A table column whose numbers arrive already
  formatted ("1,901.70", "+3.4%", "₹25,575", "12.4×", "1,625.48 (−14.5%)") was read by its type,
  text, so it sat left-aligned in the tertiary ink like a column of labels, beside the right-aligned
  numbers of the same table. A column whose every value is a written number (a dash for a missing
  one allowed) is now a numeric column: right-aligned, tabular, in the primary ink, and one the
  table colours by sign takes its colour from the written sign. The label column stays a label,
  whatever it holds. Brought from VAAYDO, where it was built.

## [v2.0.17] - 2026-11-18
### Fixed
- **The appearance switch reaches the rail's foot.** The rail is meant to read identity →
  controls → settings, with the Slate / Paper switch pinned to its foot. It stayed under the last
  control instead in every app whose rail is shorter than the window: the rail's content column
  was only as tall as its content, so there was nothing to push against, and Streamlit 1.52 wraps
  a keyed container in a layout wrapper, so the pin sat on the inner block rather than on the
  column's item. The column now fills the rail and the wrapper takes the pin; a rail taller than
  the window scrolls as before. Found while bringing VAAYDO into the family.

## [v2.0.16] - 2026-11-17
### Fixed
- **Chart tooltips print rounded numbers.** Plotly.js 3.1, which Streamlit bundles, rejects a
  number format that pairs the sign flag with a fixed precision (`%{y:+.2f}`) and prints the raw
  float in its place: a tooltip read "Consensus : 0.2295574715461816 · NEUTRAL". Plain formats
  (`.2f`) were never affected, so the leak sat only in the signed readings. Every chart now passes
  through `fix_hover_formats` on its way to the page, which formats each signed value in Python
  and hands Plotly the finished string; a unified tooltip's header (the axis value) is rounded the
  same way. Measured by sweeping the pointer across every chart on every page.

## [v2.0.15] - 2026-11-16
### Fixed
- **The cursor and typed search text are visible on Paper.** Streamlit's base theme is the dark
  one, and its inputs carried that theme's near-white text colour into two places the theme never
  named: the blinking cursor in every text, number and date field, and the characters typed into
  a dropdown to filter it ("Select transaction", "Select security"). On Paper's white fields both
  measured 1.2:1, all but invisible. Both now take the page's ink: 17.7:1 on Paper, unchanged on
  Slate. A dropdown keeps its hidden cursor; the letters you type are their own feedback.

## [v2.0.14] - 2026-11-14
### Fixed
- **A rail button's label is sized for the button.** Every button in the sidebar is a full-width
  44px action, but its label was 10px, the size of the 30px buttons in the page and the 24px
  theme toggle, so "RUN ANALYSIS" filled 79 of its 195px. The rail's buttons now carry the type
  scale's 12px. Where the rail narrows to 200px (1024px and below) the tracking closes from
  0.08em to 0.04em so the longest label still sits on one line. The theme toggle, the collapse
  arrow and the compact buttons in the page are unchanged.

## [v2.0.13] - 2026-11-14
### Fixed
- **The sidebar stays open while you use a pop-up drawn from it on a phone.** Below 768px
  Streamlit collapses the sidebar on any press outside it, so a tap on the page dismisses the
  rail. A date picker's calendar is drawn in a pop-up layer outside the sidebar, so on a phone the
  first tap on a day or a month arrow counted as "outside" and the whole sidebar closed under the
  finger. Every pop-up now keeps its presses to itself, as dropdown menus always did, and only
  below 768px; a tap on the page beside the sidebar still dismisses it. The script that does this
  rides in a zero-height frame lifted out of the layout, so no block on any page moves.

## [v2.0.12] - 2026-11-14
### Fixed
- **Every label in the system's own faces.** Measured in all eight apps: every button, segmented
  control, tab and expander title rendered its label in Streamlit's Source Sans at 14-16px (the
  control was styled, but Streamlit wraps the label in a container that sets its own font). Labels
  now inherit their control's face; the ticker's separators, slider values and multiselect tags
  take the system's mono; one widget micro-label everywhere; page names at the rail's 12px; titles
  break into balanced lines instead of leaving one word on the last line.
- **One vertical rhythm.** A section's rule sat 24-72px below the block above it depending on what
  that block was; KPI cards sat flush on the panel below them; stacked card rows touched. Now:
  blocks in a section 16px apart, a boundary (section rule, page footer) 40px below the block
  above, a header 24px above its first block, a caption 8px under the block it describes. No
  doubled rule under a tab bar.
- **Rows keep one line and one height.** Cards in a row share the row's height (a row read
  162/132/132/147/147px); a row of buttons no longer drops its last button onto a line of its own
  on a tablet, and its buttons match when one label wraps.
- Section titles in Title Case and descriptions in sentence case throughout.

## [v2.0.11] - 2026-11-14
### Fixed
- **Nothing hidden under a panel's header band.** Streamlit slides the element after a markdown
  header 16px up beneath it; once the header took Pragyam's opaque band, that covered the top of
  charts drawn right under it (subplot titles, the labels of reference lines placed above the
  plot). A chart under a header now starts below the band, with its own 8px of air.
- **Column headings sit on the band's rule.** A table under a header row that also holds the
  window strip started 10px below the band; it now sits directly on the rule, as under every
  other header.
- **Values and names at the plot's edge are drawn whole** (they were cut by Plotly's plot-area
  clip), and **reference-line labels take their tone at full strength** (some reused their line's
  25% tint).

## [v2.0.10] - 2026-11-14
### Changed
- **Pragyam's panel chrome, across the family.** Every chart, table and readout panel's header
  (its context line, meta and chip) sits on a tinted band above a rule, as Pragyam's always did,
  so a panel reads as a labelled object and its content starts below the band; seven apps drew
  the header on the panel's own ground, where it ran into the first table row or the top of the
  plot. A header that shares its row with a window strip tints the whole row.
- **Pragyam's table rhythm.** Tables take 30px rows (were 27px in most apps) with the cell padding
  derived from the row height, so every row is exactly the height its frame is sized for: no
  clipped last row, and no blank strip under it.

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

Institutional-grade analytics, benchmark comparison, advanced metrics.

### Added
- Institutional-grade analytics engine with 30+ performance metrics
- NIFTY 50 benchmark comparison with Alpha, Beta, R-Squared, Tracking Error
- Advanced risk metrics: Sharpe, Sortino, Calmar, VaR, CVaR, Information Ratio
- Rolling analytics (Sharpe and Beta with dynamic windows)
- Monthly returns heatmap with YTD column
- Drawdown analysis with underwater equity curve
- Holding attribution analysis

---

## [v1.0.0] - Initial Release

### Added
- Initial release with portfolio tracking and basic analytics
- Real-time price fetching from Yahoo Finance
- Dashboard mode with performance analysis and holdings analytics
- Excel data import and export functionality
