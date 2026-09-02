
# -*- coding: utf-8 -*-
"""
SAMHITA (संहिता) - Portfolio Tracker | A @thebullishvalue Product
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Real-time portfolio analytics with performance tracking.
Time series analysis and historical performance insights.

UI — "Obsidian Quant" Institutional Research Terminal design language.
"""

from __future__ import annotations

import html as _html
import sys
import time
import uuid
from datetime import date, datetime, timedelta, timezone
from io import BytesIO
from typing import Any, NamedTuple

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

from ui.theme import (
    COMPANY,
    PRODUCT_NAME,
    TIMEFRAMES,
    VERSION,
    chart_color,
    apply_default_hover,
    chart_layout,
    chart_rgba,
    inject_css,
    ink,
    ink_muted,
    ink_subtle,
    panel_bg,
    progress_bar,
    style_axes,
)
from ui.components import (
    render_chart_panel,
    render_control_hint,
    render_empty_state,
    render_kpi_strip,
    render_metric_card,
    render_nav_brand,
    render_notice_rail,
    render_note,
    render_rail_readout,
    render_section_header,
    render_sub_header,
    render_table_panel,
    render_ticker,
    render_top_bar,
)

# VERSION / PRODUCT_NAME / COMPANY come from ui.theme — one source of identity
# for the masthead, the footer and the rail readout. The local copies that used
# to live here had drifted (a stale version, an empty product name).

# ── In-chart type ───────────────────────────────────────────────────────────
# Plotly cannot read the stylesheet, so the data face is named here — once, at
# the app's own tiers. A bar's value label is a FIGURE, so it is mono with
# tabular numerals like every other figure in the app. Without the family
# named, Plotly falls back to its own sans and the label sits beside a mono
# axis tick as visibly a different kind of text.
CHART_FONT = "JetBrains Mono, monospace"

# ── Chart sizing scale ──────────────────────────────────────────────────────
# Three tiers. Pick the tier that matches the chart's ROLE, not its data —
# that is what keeps the page on one vertical rhythm.
CHART_HEIGHT_SM = 280   # compact 2-col (gainers/losers, rolling metrics)
CHART_HEIGHT_MD = 360   # regular 2-col (drawdown, distribution, treemaps)
CHART_HEIGHT_LG = 440   # full-width (scatter, waterfall, attribution)

# Margin presets — intent-named, picked by chart anatomy rather than by feel.
# The panel system supplies the title and context above the plot, so none of
# these reserve room for an in-plot title.
CHART_MARGIN = dict(l=10, r=10, t=16, b=44)
CHART_MARGIN_BAR = dict(l=10, r=60, t=16, b=44)      # right room for value labels
CHART_MARGIN_ROTATED = dict(l=10, r=10, t=16, b=64)  # rotated x-ticks
CHART_MARGIN_NOAXIS = dict(l=6, r=6, t=10, b=10)     # treemap
CHART_MARGIN_NOTITLE = dict(l=10, r=10, t=12, b=44)
CHART_MARGIN_HEATMAP = dict(l=10, r=10, t=44, b=16)  # top-axis heatmap

# The two appearances. Both are reading surfaces — Paper is the light one you
# read a result on and print from, Slate the dark one you work on.
#
# PAPER LEADS, and the order IS the default: `theme_choice()` falls back to
# APPEARANCES[0] for any unset or unrecognised value, so first-in-tuple is
# first-run. Kept as one fact rather than a separate DEFAULT_ constant so the
# toggle's left-to-right order and the default can never disagree.
#
# THE INVARIANT: `.streamlit/config.toml`'s `base` MUST name this same
# appearance. That file is static and cannot follow the in-app toggle, so
# whichever appearance loads FIRST is the one whose Streamlit-native widgets
# must already be correct. Get it backwards and the very first paint puts one
# theme's ink on the other theme's ground.
APPEARANCES = ("Paper", "Slate")

_THEME_CHOICE = "samhita_appearance"


# ===========================================================================
# TERMINAL LOG — curated, colored console output for the data pipeline.
#
# Writes directly to stdout (visible in the terminal running `streamlit run`).
# All UI-facing fetch chatter (native warnings/spinners) is routed here so the
# Streamlit surface stays cohesive with the app's UI/UX fidelity.
# ===========================================================================

try:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# Silence yfinance's own console chatter (HTTP errors, "Failed download",
# FutureWarnings) so SAMHITA's curated terminal log stays clean. Genuine
# failures are still captured and reported via the _Console below.
import logging as _logging
import warnings as _warnings

_logging.getLogger("yfinance").setLevel(_logging.CRITICAL)
_warnings.filterwarnings("ignore", category=FutureWarning, module="yfinance")
# yfinance raises some FutureWarnings at the caller's line, so also match by
# message (module-agnostic) — e.g. the auto_adjust default-change notice.
_warnings.filterwarnings("ignore", message=r".*auto_adjust.*")

_SESSION_RUN_ID = f"{datetime.now():%Y%m%d_%H%M%S}_{str(uuid.uuid4())[:8]}"


class _Console:
    """Minimal styled console logger (Nishkarsh-style) for SAMHITA's pipeline."""

    _USE_COLOR = bool(getattr(sys.stdout, "isatty", lambda: False)())

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    CYAN = "\033[96m"
    GRAY = "\033[90m"

    def _c(self, code: str, text: str) -> str:
        return f"{code}{text}{self.RESET}" if self._USE_COLOR else text

    def _write(self, message: str = "") -> None:
        try:
            sys.stdout.write(message + "\n")
            sys.stdout.flush()
        except Exception:
            pass

    def _ts(self) -> str:
        return datetime.now().strftime("%H:%M:%S")

    def line(self, char: str = "─", length: int = 70) -> None:
        self._write(self._c(self.GRAY, char * length))

    def section(self, title: str) -> None:
        """Open a titled data-pipeline section with the run id + timestamp."""
        self._write()
        self.line("═", 70)
        self._write("  " + self._c(self.BOLD + self.CYAN, title))
        self._write(
            "  " + self._c(self.GRAY, f"Run {_SESSION_RUN_ID} · {self._ts()}")
        )
        self.line("═", 70)

    def step(self, title: str) -> None:
        self._write("  " + self._c(self.BOLD + self.BLUE, f"▸ {title}"))

    def detail(self, message: str) -> None:
        self._write("    " + self._c(self.CYAN, "→") + f" {message}")

    def item(self, label: str, value: Any, indent: int = 6) -> None:
        self._write(f"{' ' * indent}{self._c(self.GRAY, label + ':')} {value}")

    def success(self, message: str) -> None:
        self._write("    " + self._c(self.GREEN, "✓") + f" {message}")

    def warning(self, message: str) -> None:
        self._write("    " + self._c(self.YELLOW, "⚠") + f" {message}")

    def error(self, message: str) -> None:
        self._write("    " + self._c(self.RED, "✗") + f" {message}")

    def summary(self, title: str, data: dict[str, Any]) -> None:
        self._write()
        self._write("  " + self._c(self.GRAY, f"┌─ {title}"))
        for key, value in data.items():
            self._write("  " + self._c(self.GRAY, f"│   {key}:") + f" {value}")
        self._write("  " + self._c(self.GRAY, "└─"))


log = _Console()


def _fmt_symlist(symbols: list[str], cap: int = 12) -> str:
    """Compact, capped symbol list for terminal output."""
    if not symbols:
        return "none"
    shown = ", ".join(symbols[:cap])
    extra = len(symbols) - cap
    return f"{shown} (+{extra} more)" if extra > 0 else shown


# Sentinel set by fetch_current_prices' body, which executes only on a cache
# MISS. calculate_metrics uses it to log the PRICE RESOLUTION summary exactly
# once per real fetch — not on cache-hit reruns (Streamlit double-runs the
# script on load), which would otherwise duplicate the summary block.
_FETCH_RAN: dict[str, bool] = {"primary": False}


# Map a portfolio symbol to a yfinance ticker.
# Symbols WITHOUT a '.' get the .NS (NSE) suffix as a fallback (e.g. RELIANCE -> RELIANCE.NS).
# Symbols that ALREADY contain a '.' are exchange-qualified and used exactly as-is
# (e.g. NSDL.BO -> NSDL.BO, QUEST.BO -> QUEST.BO).
def _to_yf_ticker(symbol: str) -> str:
    return symbol if '.' in symbol else f"{symbol}.NS"


# ---------------------------------------------------------------------------
# Market data resolution — tiered source hierarchy.
#
# Sources are ordered by ROBUSTNESS and BATCH REACH, not by convenience.
# Every tier is optional and lazily imported: a missing or failing tier is
# skipped and the chain degrades to the next one, so the app always resolves
# to the best data actually available.
#
#   TIER 1  Yahoo batch quote   1 HTTP call for N symbols. Returns last +
#           (yf /v7/quote)      previousClose + marketState. Authoritative
#                               previous close (validated 32/32 against the
#                               NSE bhavcopy). Live intraday.
#
#   TIER 2  Yahoo batch history 1 HTTP call for N symbols. Same session as
#           (yf.download 5d)    tier 1 but derives values from daily OHLC
#                               bars, which Yahoo sometimes serves with whole
#                               sessions missing — so it is a structural
#                               backstop for tier 1, never the prime source
#                               of a previous close.
#
#   TIER 3  Exchange EOD        1 file per exchange covering every scrip
#           bhavcopy (NSE/BSE)  (~3.6k NSE / ~5k BSE rows). Official exchange
#                               data, the most trustworthy numbers in the
#                               chain — but END OF DAY only. Accepted
#                               immediately when the file is for TODAY (the
#                               session has closed, so EOD *is* current);
#                               otherwise held as a provisional backstop so a
#                               stale close never masquerades as a live price.
#
#   TIER 4  Per-symbol live     N HTTP calls (NSE) or 2N (BSE: scrip-code
#           (NseKit / bse)      lookup + quote). Fresh but slow and the most
#                               failure-prone, so it runs LAST and only for
#                               symbols every batch tier left unresolved.
#
# The portfolio SYMBOL convention is unchanged: no dot -> NSE, ".NS" -> NSE,
# ".BO" -> BSE.
# ---------------------------------------------------------------------------

class Quote(NamedTuple):
    """One resolved market quote and its provenance."""
    last: float          # latest traded / closing price
    prev_close: float    # previous session's close (today-change basis)
    source: str          # tier label, for the resolution log
    asof: date | None    # session the data represents; None = live/unknown

    @property
    def ok(self) -> bool:
        """True when this quote carries a usable last price."""
        return not pd.isna(self.last)


def _classify(symbol: str) -> tuple[str, str] | None:
    """Map a raw portfolio symbol to (exchange, bare_symbol).

    Mirrors _to_yf_ticker: no dot or ".NS" -> NSE; ".BO" -> BSE.
    Returns None for symbols/exchanges we have no secondary source for.
    """
    if not symbol or not isinstance(symbol, str):
        return None
    s = symbol.strip().upper()
    if '.' not in s:
        return ('NSE', s)
    if s.endswith('.NS'):
        return ('NSE', s[:-3])
    if s.endswith('.BO'):
        return ('BSE', s[:-3])
    return None


def _num(value: Any) -> float:
    """Best-effort float parse; returns NaN for blanks/None/garbage."""
    try:
        if value is None:
            return np.nan
        if isinstance(value, str):
            value = value.replace(',', '').strip()
            if value in ('', '-'):
                return np.nan
        return float(value)
    except (ValueError, TypeError):
        return np.nan


# --- TIER 1 ---------------------------------------------------------------
# One request for every symbol. This is both the fastest and the most
# complete source: it is the only one that hands us an authoritative
# previousClose without inferring it from a bar series.

_YAHOO_QUOTE_URL = "https://query2.finance.yahoo.com/v7/finance/quote"


def _tier1_yahoo_quote(symbols: list[str]) -> dict[str, Quote]:
    """Yahoo batch quote: one call for all symbols."""
    out: dict[str, Quote] = {}
    if not symbols:
        return out
    ticker_map = {_to_yf_ticker(s): s for s in symbols}
    params = {
        "symbols": ",".join(ticker_map),
        "fields": ("regularMarketPrice,regularMarketPreviousClose,"
                   "marketState,regularMarketTime"),
    }
    # RETRIED ONCE, on a fresh client. This tier is the only source that states
    # a previous close outright, and losing it demotes the whole portfolio to a
    # basis that has to be repaired afterwards — so a transient failure is
    # worth one more attempt rather than a tier's worth of degradation.
    # yfinance holds a process-wide session with a cookie/crumb it refreshes
    # lazily, and a rerun landing mid-refresh is the observed intermittent
    # failure; a second call after that refresh completes succeeds.
    results: list = []
    last_err: Exception | None = None
    for attempt in (1, 2):
        try:
            payload = yf.YfData().get_raw_json(_YAHOO_QUOTE_URL, params=params)
            results = (payload or {}).get("quoteResponse", {}).get("result", []) or []
            if results:
                break
            last_err = RuntimeError("empty quoteResponse")
        except Exception as e:      # noqa: BLE001 — any failure is retryable here
            last_err = e
        if attempt == 1:
            time.sleep(0.6)
    if not results:
        # The MESSAGE, not just the class. A bare "(AttributeError)" said a
        # tier was down without saying why, and this tier going down quietly is
        # what put the portfolio on a mixed basis in the first place.
        log.warning(f"Yahoo batch quote unavailable after 2 tries "
                    f"({type(last_err).__name__}: {last_err}); using history")
        return out

    states: set[str] = set()
    for row in results:
        orig = ticker_map.get(row.get("symbol", ""))
        if not orig:
            continue
        last = _num(row.get("regularMarketPrice"))
        prev = _num(row.get("regularMarketPreviousClose"))
        if not pd.isna(last):
            out[orig] = Quote(last, prev, "yahoo:quote", None)
        if row.get("marketState"):
            states.add(str(row["marketState"]))
    if states:
        log.detail(f"Market state · {'/'.join(sorted(states))}")
    return out


# --- TIER 2 ---------------------------------------------------------------
# One request for every symbol, but built from daily OHLC bars. Yahoo drops
# whole sessions from this endpoint for some tickers, so the previous close is
# taken as the last valid bar STRICTLY BEFORE the latest one, per column —
# never by blind positional indexing, which silently yields NaN or a
# multi-session gap when a bar is missing.

def _tier2_yahoo_history(symbols: list[str]) -> dict[str, Quote]:
    """Yahoo batch daily history: one call for all symbols."""
    out: dict[str, Quote] = {}
    if not symbols:
        return out
    ticker_map = {_to_yf_ticker(s): s for s in symbols}
    try:
        data = yf.download(tickers=list(ticker_map), period="5d",
                           progress=False, auto_adjust=False)
        if data is None or data.empty:
            return out
        if 'Close' not in data.columns.get_level_values(0):
            return out
        close = data['Close']
    except Exception as e:
        log.warning(f"Yahoo batch history failed ({type(e).__name__})")
        return out

    if isinstance(close, pd.Series):          # single-ticker shape
        close = close.to_frame(name=list(ticker_map)[0])

    for ticker, orig in ticker_map.items():
        if ticker not in close.columns:
            continue
        series = close[ticker].dropna()
        if series.empty:
            continue
        last = float(series.iloc[-1])
        prev = float(series.iloc[-2]) if len(series) >= 2 else np.nan
        asof = series.index[-1].date() if hasattr(series.index[-1], 'date') else None
        out[orig] = Quote(last, prev, "yahoo:history", asof)
    return out


# --- TIER 3 ---------------------------------------------------------------
# One file per exchange, covering every scrip the exchange traded that day.
# Official numbers, but end-of-day: only current once the session has closed.

def _bhav_session_date(df: pd.DataFrame) -> "date | None":
    """The session a bhavcopy frame actually covers, read from its own TradDt.

    THE DATE MUST COME FROM THE DATA. Asking the archive for a date and then
    trusting that date is what let a file for one session be labelled with
    another: NSE has no bhavcopy for a session that has not settled, the
    downloader saves whatever the URL returned under the requested filename,
    and the caller then reported the date it wanted rather than the date it
    got. Everything downstream — the freshness gate especially — is only as
    honest as this value.
    """
    if df is None or 'TradDt' not in df.columns:
        return None
    try:
        stamps = pd.to_datetime(df['TradDt'], errors='coerce').dropna()
        return stamps.iloc[0].date() if len(stamps) else None
    except (TypeError, ValueError):
        return None


def _bhav_lookup(df: pd.DataFrame, eq_only: bool) -> dict[str, tuple[float, float]]:
    """Build {TckrSymb: (close, prev_close)} from a UDiFF bhavcopy frame."""
    lookup: dict[str, tuple[float, float]] = {}
    if df is None or 'TckrSymb' not in df.columns:
        return lookup
    rows = df
    if eq_only and 'SctySrs' in df.columns:
        rows = df[df['SctySrs'].astype(str).str.strip() == 'EQ']
    for r in rows.itertuples():
        sym = str(getattr(r, 'TckrSymb', '')).strip()
        if sym and sym not in lookup:
            lookup[sym] = (_num(getattr(r, 'ClsPric', None)),
                           _num(getattr(r, 'PrvsClsgPric', None)))
    return lookup


def _nse_bhavcopy() -> tuple[dict[str, tuple[float, float]], date | None]:
    """Most recent NSE EOD bhavcopy (jugaad). Returns (lookup, session_date)."""
    try:
        import tempfile
        from jugaad_data.nse import bhavcopy_save
    except Exception:
        return {}, None
    folder, today = tempfile.gettempdir(), datetime.now().date()
    for back in range(0, 7):
        d = today - timedelta(days=back)
        try:
            df = pd.read_csv(bhavcopy_save(d, folder))
            df.columns = [c.strip() for c in df.columns]
            got = _bhav_session_date(df)
            lookup = _bhav_lookup(df, eq_only=True)
            if not lookup or got is None:
                continue
            if got != d:
                # The archive answered with a DIFFERENT session than the one
                # asked for — on a date with no bhavcopy yet the downloader
                # will happily save an error page, or the previous session's
                # file, under the requested name and cache it there. Skip it
                # and let the loop ask for the session it actually is.
                log.detail(f"NSE bhavcopy asked {d:%d-%b} · file is {got:%d-%b}; "
                           f"using the file's own session")
            log.detail(f"NSE bhavcopy {got:%d-%b-%Y} · {len(lookup)} scrips")
            return lookup, got
        except Exception:
            continue
    log.warning("NSE bhavcopy unavailable (last 7 days)")
    return {}, None


def _bse_bhavcopy() -> tuple[dict[str, tuple[float, float]], date | None]:
    """Most recent BSE EOD bhavcopy. Returns (lookup, session_date)."""
    try:
        import tempfile
        from bse import BSE
        b = BSE(download_folder=tempfile.gettempdir())
    except Exception:
        return {}, None
    try:
        today = datetime.now().date()
        for back in range(0, 7):
            d = today - timedelta(days=back)
            try:
                df = pd.read_csv(b.bhavcopyReport(d))
                df.columns = [c.strip() for c in df.columns]
                got = _bhav_session_date(df)
                lookup = _bhav_lookup(df, eq_only=False)
                if not lookup or got is None:
                    continue
                log.detail(f"BSE bhavcopy {got:%d-%b-%Y} · {len(lookup)} scrips")
                return lookup, got
            except Exception:
                continue
        log.warning("BSE bhavcopy unavailable (last 7 days)")
        return {}, None
    finally:
        try:
            b.exit()
        except Exception:
            pass


def _tier3_bhavcopy(symbols: list[str]) -> dict[str, Quote]:
    """Exchange EOD bhavcopy: one bulk file per exchange."""
    out: dict[str, Quote] = {}
    by_exch: dict[str, dict[str, str]] = {'NSE': {}, 'BSE': {}}
    for s in symbols:
        c = _classify(s)
        if c:
            by_exch[c[0]][c[1]] = s
    for exch, loader in (('NSE', _nse_bhavcopy), ('BSE', _bse_bhavcopy)):
        wanted = by_exch[exch]
        if not wanted:
            continue
        lookup, session = loader()
        for bare, orig in wanted.items():
            hit = lookup.get(bare)
            if hit and not pd.isna(hit[0]):
                out[orig] = Quote(hit[0], hit[1], f"{exch.lower()}:bhavcopy", session)
    return out


# --- TIER 4 ---------------------------------------------------------------
# Per-symbol network calls. Fresh, but N (NSE) to 2N (BSE) requests and the
# most brittle links in the chain, so this runs last on whatever is left.

def _tier4_nse_live(bare_to_orig: dict[str, str]) -> dict[str, Quote]:
    """NseKit live quotes, one call per symbol."""
    out: dict[str, Quote] = {}
    try:
        from NseKit import Nse
        nse = Nse()
    except Exception as e:
        log.warning(f"NseKit unavailable ({type(e).__name__}); skipping NSE live")
        return out
    for bare, orig in bare_to_orig.items():
        try:
            d = nse.cm_live_equity_full_info(bare)
            if d:
                last = _num(d.get('LastTradedPrice'))
                if not pd.isna(last):
                    out[orig] = Quote(last, _num(d.get('PreviousClose')),
                                      "nse:live", None)
                    log.detail(f"NseKit · {bare} → {last}")
        except Exception:
            continue
    return out


def _tier4_bse_live(bare_to_orig: dict[str, str]) -> dict[str, Quote]:
    """bse.quote live quotes, scrip code resolved per symbol."""
    out: dict[str, Quote] = {}
    try:
        import tempfile
        from bse import BSE
        b = BSE(download_folder=tempfile.gettempdir())
    except Exception as e:
        log.warning(f"bse unavailable ({type(e).__name__}); skipping BSE live")
        return out
    try:
        for bare, orig in bare_to_orig.items():
            try:
                code = b.getScripCode(bare)
                if not code:
                    continue
                q = b.quote(code)
                if q:
                    last = _num(q.get('LTP'))
                    if not pd.isna(last):
                        out[orig] = Quote(last, _num(q.get('PrevClose')),
                                          "bse:live", None)
                        log.detail(f"bse · {bare} (#{code}) → {last}")
            except Exception:
                continue
    finally:
        try:
            b.exit()
        except Exception:
            pass
    return out


def _tier4_per_symbol(symbols: list[str]) -> dict[str, Quote]:
    """Per-symbol live quotes across both exchanges."""
    nse: dict[str, str] = {}
    bse: dict[str, str] = {}
    for s in symbols:
        c = _classify(s)
        if c:
            (nse if c[0] == 'NSE' else bse)[c[1]] = s
    out: dict[str, Quote] = {}
    if nse:
        log.detail(f"NSE live (NseKit) · {len(nse)} symbol(s)")
        out.update(_tier4_nse_live(nse))
    if bse:
        log.detail(f"BSE live (bse.quote) · {len(bse)} symbol(s)")
        out.update(_tier4_bse_live(bse))
    return out


# --- Resolver -------------------------------------------------------------

_TIERS: tuple[tuple[str, str, Any], ...] = (
    ("TIER 1", "Yahoo batch quote      · 1 call, all symbols", _tier1_yahoo_quote),
    ("TIER 2", "Yahoo batch history    · 1 call, all symbols", _tier2_yahoo_history),
    ("TIER 3", "Exchange EOD bhavcopy  · 1 file per exchange", _tier3_bhavcopy),
    ("TIER 4", "Per-symbol live quotes · 1 call per symbol",   _tier4_per_symbol),
)



#: Sources whose previous close is the previous SESSION's close, stated by the
#: venue or by the quote itself. Everything else infers it.
_AUTHORITATIVE_PREV = frozenset({
    "yahoo:quote", "nse:live", "bse:live", "nse:bhavcopy", "bse:bhavcopy",
})


def _repair_prev_close(resolved: dict[str, Quote]) -> None:
    """Replace an inferred previous close with the exchange's own.

    `yahoo:history` cannot state a previous SESSION — it steps back to the
    previous available BAR, and Yahoo's daily series drops whole sessions for
    some tickers. Measured on this portfolio: 20 of 32 holdings had no bar for
    the last settled session, so their "previous close" was two sessions old
    and today's change was silently a two-day change. That is the whole reason
    the same portfolio, on the same data, read -0.54% when the quote API
    answered and -0.95% when it did not — and why the figure moved whenever a
    transient Yahoo failure changed which tier answered.

    The exchange bhavcopy settles it exactly: for a session still in progress,
    the previous close IS the last SETTLED session's close. So a bhavcopy that
    was too stale to PRICE a holding is precisely the right BASIS for it — the
    two uses have opposite freshness requirements, which is why one pass could
    never serve both. Verified 32/32 against the quote API's own previousClose.

    Only runs when something actually needs repairing, so the healthy path
    (quote answers for everything) costs no extra download.
    """
    needy = [s for s, q in resolved.items()
             if q.source not in _AUTHORITATIVE_PREV]
    if not needy:
        return

    today = datetime.now().date()
    by_exch: dict[str, dict[str, str]] = {'NSE': {}, 'BSE': {}}
    for sym in needy:
        c = _classify(sym)
        if c:
            by_exch[c[0]][c[1]] = sym

    fixed = 0
    for exch, loader in (('NSE', _nse_bhavcopy), ('BSE', _bse_bhavcopy)):
        wanted = by_exch[exch]
        if not wanted:
            continue
        lookup, session = loader()
        if not lookup or session is None:
            continue
        for bare, sym in wanted.items():
            hit = lookup.get(bare)
            if not hit:
                continue
            # A settled session BEFORE today: its close is today's basis.
            # Today's own settled file: its PrvsClsgPric is.
            basis = hit[0] if session < today else hit[1]
            if pd.isna(basis):
                continue
            q = resolved[sym]
            if not pd.isna(q.prev_close) and abs(q.prev_close - basis) < 0.005:
                continue
            resolved[sym] = q._replace(prev_close=float(basis))
            fixed += 1
    if fixed:
        log.detail(f"Previous close repaired from exchange settlement · "
                   f"{fixed} holding(s)")


@st.cache_data(ttl=300, show_spinner=False)
def resolve_quotes(symbols: tuple[str, ...]) -> dict[str, Quote]:
    """Resolve {symbol: Quote} by walking the source hierarchy in order.

    Each tier is asked only for the symbols still unresolved after the tiers
    above it, so the cheap batch sources carry the whole portfolio and the
    per-symbol tier is reached only by genuine stragglers.

    An end-of-day bhavcopy quote is accepted outright only when its file is
    for today — the session has closed, so the EOD close *is* the current
    price. A bhavcopy from an earlier session is banked as a provisional
    backstop and the walk continues, so a stale close can never be presented
    as a live price while a fresher source is still reachable.
    """
    symbols = [s for s in symbols if s and isinstance(s, str)]
    if not symbols:
        return {}

    _FETCH_RAN["primary"] = True
    log.section("SAMHITA · MARKET DATA")

    resolved: dict[str, Quote] = {}
    provisional: dict[str, Quote] = {}
    today = datetime.now().date()

    for tag, label, fetch in _TIERS:
        pending = [s for s in symbols if s not in resolved]
        if not pending:
            break
        log.step(f"{tag} · {label} · {len(pending)} pending")
        t0 = time.perf_counter()
        try:
            got = fetch(pending)
        except Exception as e:
            log.error(f"{tag} raised {type(e).__name__}: {e}")
            got = {}

        accepted = 0
        for sym, q in got.items():
            if sym in resolved or not q.ok:
                continue
            # EOD data is only "current" once the session it covers has ended.
            if q.asof is not None and q.asof < today:
                provisional.setdefault(sym, q)
                continue
            resolved[sym] = q
            accepted += 1

        dt = time.perf_counter() - t0
        held = len(provisional) - sum(1 for s in provisional if s in resolved)
        note = f" · {held} held as stale backstop" if held and tag == "TIER 3" else ""
        log.success(f"{tag} resolved {accepted}/{len(pending)} in {dt:.1f}s{note}")

    # Anything still unresolved falls back to the freshest stale quote we saw.
    backstopped: list[str] = []
    for sym, q in provisional.items():
        if sym not in resolved:
            resolved[sym] = q
            backstopped.append(sym)
    if backstopped:
        stale = provisional[backstopped[0]]
        log.warning(f"No live source responded for {len(backstopped)} symbol(s); "
                    f"using stale {stale.source} ({stale.asof}) close as the price")
        log.item("Backstopped", _fmt_symlist(sorted(backstopped)))

    # The PRICE is now settled; the BASIS may not be. A holding priced from a
    # bar series carries an inferred previous close, and that is the one input
    # today's change cannot afford to have guessed.
    _repair_prev_close(resolved)

    unresolved = [s for s in symbols if s not in resolved]
    by_source: dict[str, int] = {}
    for q in resolved.values():
        by_source[q.source] = by_source.get(q.source, 0) + 1
    log.summary("PRICE RESOLUTION", {
        "Holdings": len(symbols),
        **{k: v for k, v in sorted(by_source.items())},
        "Unresolved": f"{len(unresolved)}" + (
            f" ({_fmt_symlist(unresolved)})" if unresolved else ""),
    })
    log.line("═", 70)
    return resolved
# Current price + previous close are two views of the SAME resolved quote, so
# both go through one cached walk of the hierarchy rather than two independent
# fetches that could disagree with each other.
def fetch_current_prices(symbols: list[str]) -> dict[str, float | Any]:
    """Latest traded price per symbol, via the tiered source hierarchy."""
    quotes = resolve_quotes(tuple(symbols))
    return {s: (quotes[s].last if s in quotes else np.nan) for s in symbols}

# Function to load data
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame | None:
    """Load portfolio data from Excel file."""
    file_path = "Summary Report.xlsx"
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        return None

def fetch_previous_close(symbols: list[str]) -> dict[str, float | Any]:
    """Previous-session close per symbol, via the tiered source hierarchy.

    This is the basis for today's change, so it comes from the same Quote as
    the current price — never from a separate positional lookup into a bar
    series that may be missing the session entirely.
    """
    quotes = resolve_quotes(tuple(symbols))
    return {s: (quotes[s].prev_close if s in quotes else np.nan) for s in symbols}
# Function to calculate metrics
def calculate_metrics(
    df: pd.DataFrame,
    progress: Any = None,
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Calculate portfolio performance metrics.

    ``progress`` is an optional callable ``(pct, label, sub="")`` used to drive
    the themed UI progress card; it is a no-op when None.
    """
    def _p(pct: int, label: str, sub: str = "") -> None:
        if progress:
            progress(pct, label, sub)

    df = df.copy()
    symbols = df['SYMBOL'].tolist()

    _FETCH_RAN["primary"] = False  # set True only if the fetch actually runs
    _p(20, "Resolving Market Data", f"tiered sources · {len(symbols)} holdings")

    # One cached walk of the source hierarchy yields both the current price and
    # the previous close, so the two can never come from disagreeing sources.
    quotes = resolve_quotes(tuple(symbols))
    price_map = {s: (quotes[s].last if s in quotes else np.nan) for s in symbols}
    prev_close_map = {s: (quotes[s].prev_close if s in quotes else np.nan)
                      for s in symbols}
    # Which tier answered, and for which session. Carried onto the frame so the
    # notice rail can say what the numbers rest on — a run that quietly fell to
    # a lesser source is exactly the run whose figures deserve a caveat.
    source_map = {s: (quotes[s].source if s in quotes else "") for s in symbols}
    asof_map = {s: (quotes[s].asof if s in quotes else None) for s in symbols}

    _p(90, "Computing Analytics", f"{len(symbols)} holdings")

    # 3. Update CURRENT PRICE column using resolved data
    df['FETCHED PRICE'] = df['SYMBOL'].map(price_map)
    df['CURRENT PRICE'] = df['FETCHED PRICE'].fillna(df.get('CURRENT PRICE', df['AVERAGE PRICE']))

    # 4. Previous close, the basis for today's change
    df['PREV CLOSE'] = df['SYMBOL'].map(prev_close_map)
    df['PRICE SOURCE'] = df['SYMBOL'].map(source_map)
    df['PRICE ASOF'] = df['SYMBOL'].map(asof_map)

    # 5. Perform calculations using the updated 'CURRENT PRICE'
    df['INVESTED'] = df['QUANTITY'] * df['AVERAGE PRICE']
    df['CURR. VALUE'] = df['QUANTITY'] * df['CURRENT PRICE']
    df['GAIN'] = df['CURR. VALUE'] - df['INVESTED']
    
    # Today's change per holding. This is only meaningful when the current
    # price is a REAL quote: where no source resolved, CURRENT PRICE falls back
    # to AVERAGE PRICE, and differencing a buy price against yesterday's close
    # would dump the whole lifetime P&L of that holding into "today".
    _today_ok = df['FETCHED PRICE'].notna() & df['PREV CLOSE'].notna()
    df['TODAY CHANGE'] = np.where(
        _today_ok,
        (df['CURRENT PRICE'] - df['PREV CLOSE']) * df['QUANTITY'],
        0
    )
    df['TODAY %'] = np.where(
        _today_ok & (df['PREV CLOSE'] != 0),
        (df['CURRENT PRICE'] - df['PREV CLOSE']) / df['PREV CLOSE'] * 100,
        0
    )
    
    # Avoid division by zero
    df['GAIN %'] = np.where(df['INVESTED'] != 0, df['GAIN'] / df['INVESTED'] * 100, 0)
    
    total_curr_value = df['CURR. VALUE'].sum()
    df['WT'] = np.where(total_curr_value != 0, df['CURR. VALUE'] / total_curr_value * 100, 0)
    # Contribution to the portfolio's return. Return is measured against COST,
    # so contributions must be weighted by each holding's share of cost — with
    # market-value weights the column does not sum to 'Portfolio Return %'.
    total_invested = df['INVESTED'].sum()
    df['WEIGHTED RETURN %'] = np.where(
        total_invested != 0, df['GAIN'] / total_invested * 100, 0)
    
    # Calculate today's portfolio return
    today_change_total = df['TODAY CHANGE'].sum()
    prev_portfolio_value = total_curr_value - today_change_total
    today_return_pct = (today_change_total / prev_portfolio_value * 100) if prev_portfolio_value != 0 else 0

    metrics = {
        'Total Current Value': total_curr_value,
        'Total Invested': df['INVESTED'].sum(),
        'Total Gain': df['GAIN'].sum(),
        'Portfolio Return %': np.where(df['INVESTED'].sum() != 0, df['GAIN'].sum() / df['INVESTED'].sum() * 100, 0),
        'Today Change': today_change_total,
        'Today Return %': today_return_pct,
        'Top 5 Concentration': df['WT'].nlargest(5).sum(),
        'Number of Holdings': len(df)
    }
    return df, metrics

# Function to format currency (Indian Rupee with Indian comma style)
def format_currency(value: float) -> str:
    """
    Formats a number in Indian numbering system (lakhs, crores).
    Example: 6797258.49 -> Rs 67,97,258.49
    """
    value = float(value)
    value = 0.0 if abs(value) < 0.005 else value   # avoid rendering "-Rs 0.00"
    negative = value < 0
    value = abs(value)
    
    # Split into integer and decimal parts
    integer_part = int(value)
    decimal_part = value - integer_part
    
    # Convert integer to string
    int_str = str(integer_part)
    
    # Indian numbering: first group of 3 from right, then groups of 2
    if len(int_str) <= 3:
        formatted = int_str
    else:
        # Last 3 digits
        result = int_str[-3:]
        # Remaining digits, grouped by 2 from right to left
        remaining = int_str[:-3]
        while len(remaining) > 2:
            result = remaining[-2:] + ',' + result
            remaining = remaining[:-2]
        if remaining:
            result = remaining + ',' + result
        formatted = result
    
    # Add decimal places (always show 2 decimal places)
    formatted += f"{decimal_part:.2f}"[1:]
    
    formatted = f"{'-' if negative else ''}₹{formatted}"
    return formatted


# Function to create downloadable Excel
def to_excel(df: pd.DataFrame) -> bytes:
    """Generate Excel file from DataFrame."""
    output = BytesIO()
    # Drop calculated columns that may cause issues or are redundant for a base export
    export_df = df.drop(columns=['INVESTED', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'FETCHED PRICE'], errors='ignore')
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Portfolio')
    return output.getvalue()


# ── Chart theming helper ────────────────────────────────────────────────────
def _apply_theme(fig, *, height: int = 360, show_legend: bool = False,
                 margin: dict | None = None, title: str = "",
                 x_title: str = "", y_title: str = "", axes: bool = True) -> None:
    """Apply the app's one chart grammar to a figure (mutates in place).

    ``title`` is accepted and DELIBERATELY IGNORED. Every chart renders inside
    a panel whose header names it, so an in-plot title would be that title
    again four pixels lower. The parameter survives so the call sites can keep
    documenting what each plot is without drawing it twice.

    ``axes=False`` is for the plots that HAVE no axes — treemaps and the
    heatmap. They still need the canvas, font, hover label and colourway, and
    they still need the two-decimal hover backfill; what they must not get is
    a grid, a zero line and a crosshair drawn over a tiling. Before this they
    hand-rolled their own `update_layout`, which is how they ended up carrying
    a second in-plot title and a colour or two from the retired palette.
    """
    fig.update_layout(**chart_layout(height=height, show_legend=show_legend,
                                     margin=margin or CHART_MARGIN))
    if axes:
        style_axes(fig, y_title=y_title, x_title=x_title)
    else:
        apply_default_hover(fig)


def _pad_for_value_labels(fig, *, horizontal: bool = True,
                          frac: float = 0.18) -> None:
    """Extend the value axis so labels drawn OUTSIDE the bars fit inside it.

    `textposition="outside"` puts the label past the end of its bar, and
    `cliponaxis=False` — which the tallest bar needs, or its label is sheared
    off at the axis — lets it draw past the plot area entirely. The two
    together put the longest bar's label on top of the category ticks: on Top
    Losers, FMCGIETF's bar reached the left edge and its "-9.8%" landed on the
    tick that names it.

    Neither setting is wrong; what was missing is room. A bar is measured from
    zero, so the range is anchored there and padded only on the side(s) that
    actually carry bars — a chart of gains does not reserve space to the left
    of zero for labels that will never be drawn there.

    Written per AXIS rather than per figure so it also serves the two-subplot
    contribution chart, whose halves are on different scales.
    """
    vals_by_axis: dict[str, list[float]] = {}
    for tr in fig.data:
        if getattr(tr, "type", "") != "bar":
            continue
        vals = tr.x if horizontal else tr.y
        if vals is None:
            continue
        key = (tr.xaxis or "x") if horizontal else (tr.yaxis or "y")
        for v in vals:
            try:
                f = float(v)
            except (TypeError, ValueError):
                continue
            if f == f:                      # not NaN
                vals_by_axis.setdefault(key, []).append(f)

    for key, vals in vals_by_axis.items():
        if not vals:
            continue
        lo, hi = min(min(vals), 0.0), max(max(vals), 0.0)
        span = (hi - lo) or abs(hi) or 1.0
        pad = span * frac
        rng = [lo - (pad if lo < 0 else 0.0), hi + (pad if hi > 0 else 0.0)]
        name = ("xaxis" if horizontal else "yaxis") + (key[1:] if len(key) > 1 else "")
        try:
            fig.layout[name].range = rng
        except (KeyError, ValueError):
            continue


def _gain_colorscale(series: pd.Series) -> dict:
    """Diverging colour config for a gain/loss series, from the app's palette.

    One definition for both treemaps, which previously carried two different
    scales — one of them anchored on a literal `#F07075` that belongs to no
    palette in this app. Loss → gain reads rose → accent → emerald, with the
    midpoint pinned at zero so the neutral colour always means "flat" rather
    than "middle of whatever range this portfolio happens to span".
    """
    lo, hi = float(series.min()), float(series.max())
    # Loss → flat → gain. The midpoint is the NEUTRAL slate, not the accent.
    # Accent is this system's one interactive colour — nav, primary actions,
    # focus — so spending it on "zero return" both breaks that meaning and,
    # because most holdings sit near the middle of any real portfolio, painted
    # almost every tile the same interactive blue. A neutral midpoint puts the
    # ink where the reading is: red is a loss, green is a gain, and a holding
    # that has not moved recedes.
    if lo >= 0:
        return {"color_continuous_scale": [chart_color("slate"), chart_color("emerald")],
                "range_color": [lo, hi]}
    if hi <= 0:
        return {"color_continuous_scale": [chart_color("rose"), chart_color("slate")],
                "range_color": [lo, hi]}
    # Symmetric about zero, so the same return reads the same shade whichever
    # side it falls on — otherwise one +68% outlier compresses every loss.
    _bound = max(abs(lo), abs(hi))
    return {"color_continuous_scale": [chart_color("rose"), chart_color("slate"),
                                       chart_color("emerald")],
            "range_color": [-_bound, _bound],
            "color_continuous_midpoint": 0}


def _style_treemap(fig, *, height: int) -> None:
    """The app's grammar for a treemap.

    A treemap is a tiling, so it takes the canvas, font and hover from the
    shared layout but none of the axis furniture. The tile borders are painted
    in the PANEL's own background rather than a fixed colour: that is what
    separates adjacent tiles in both appearances instead of drawing a dark
    halo on Paper. Labels are the data face, since a tile's label is a symbol.

    THE ROOT BAND IS REMOVED RATHER THAN CAMOUFLAGED. Plotly reserves space
    above a parent for its own header via ``marker.pad``, and with `path` a
    single column that parent is an implicit root carrying no reading at all —
    a strip of chrome for a label that does not exist. Painting it the panel
    colour hid it and still spent the space; zeroing the pad deletes it, and
    the tiling reclaims the full panel. That is also why none of the colour
    plumbing this used to need survives: the root is now covered by its own
    children, so it cannot show whatever colour Plotly gives it.
    """
    _apply_theme(fig, height=height, margin=CHART_MARGIN_NOAXIS, axes=False)
    fig.update_traces(
        # No header space for a root that has nothing to say. Tiles go
        # edge to edge — the panel already supplies the frame.
        marker=dict(pad=dict(t=0, l=0, r=0, b=0),
                    line=dict(color=panel_bg(), width=1)),
        # A drill-down breadcrumb, for a hierarchy exactly one level deep.
        pathbar=dict(visible=False),
        # White on every tile: each fill is a saturated rose/slate/emerald, so
        # one text colour clears contrast on all of them in BOTH appearances.
        # Inheriting the layout ink would put mid-grey type on a mid-grey tile.
        textfont=dict(family="JetBrains Mono, monospace", size=11, color="#FFFFFF"),
        # Centred, not left-aligned. A tile is a block, and its label names the
        # whole block — hung on the left edge it reads as belonging to the
        # boundary it sits against rather than to the area it labels.
        textposition="middle center",
        tiling=dict(pad=2),
        hovertemplate="<b>%{label}</b><br>%{value:,.0f}<extra></extra>",
    )
    fig.update_coloraxes(showscale=False)



# ══════════════════════════════════════════════════════════════════════════════
# APP SHELL
# ══════════════════════════════════════════════════════════════════════════════

def theme_choice() -> str:
    """The appearance the user last chose, always one of ``APPEARANCES``.

    A value that is not in the list is treated as unset. That matters across a
    rename: a session opened before this list changed still holds the old
    string in the durable key, and handing an unknown option to the segmented
    control as its default is an error rather than a fallback.
    """
    choice = st.session_state.get(_THEME_CHOICE)
    return choice if choice in APPEARANCES else APPEARANCES[0]


def _render_appearance_control() -> None:
    """The theme switch — LAST control in the rail, deliberately.

    The rail is ordered by frequency of use, and this is the least consequential
    switch in the application: Slate is the working theme, Paper is for reading
    a result and for print. Putting it under the brand mark, where it used to
    sit in apps of this shape, gives the least-used control the most valuable
    position on screen.
    """
    with st.container(key="appearance"):
        st.markdown('<div class="sidebar-title">Appearance</div>', unsafe_allow_html=True)
        mode = st.segmented_control(
            "Appearance", list(APPEARANCES), key="theme_mode",
            default=theme_choice(), label_visibility="collapsed",
            help="Slate — dark, for working. Paper — light, for reading and print.",
        )
        # Mirror the widget into the DURABLE key and rerun, so the stylesheet
        # at the top of main() is re-injected with the new value. Without the
        # rerun the change would land half-way down the page and the run would
        # render as a mix of both appearances.
        if mode is not None and mode != theme_choice():
            st.session_state[_THEME_CHOICE] = mode
            st.rerun()


def _render_footer() -> None:
    ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
    st.markdown(
        f'<div class="app-footer"><div class="content">'
        f'\u00a9 {ist_now.year} <strong>{PRODUCT_NAME}</strong> &nbsp;\u00b7&nbsp; {COMPANY}'
        f' &nbsp;\u00b7&nbsp; {VERSION} &nbsp;\u00b7&nbsp; '
        f'{ist_now.strftime("%Y-%m-%d %H:%M:%S IST")}'
        f'</div></div>',
        unsafe_allow_html=True,
    )


def _quote_notices(df: pd.DataFrame) -> list[dict]:
    """Data-quality notices for the rail under the command bar.

    These used to be full-width boxes at the very top of the page, which meant
    that on exactly the days the data most needed scrutiny the interface led
    with an apology instead of a number. One row each, below the thing they
    qualify rather than above it.
    """
    notices: list[dict] = []
    unpriced = df.loc[df['FETCHED PRICE'].isna(), 'SYMBOL'].tolist()
    if unpriced:
        notices.append({
            "kind": "warning",
            "title": "Unpriced holdings",
            "body": (f"No source returned a quote for {_fmt_symlist(unpriced)}. "
                     f"These are valued at cost and contribute nothing to today's change."),
        })
    stale = df.loc[df['PREV CLOSE'].isna(), 'SYMBOL'].tolist()
    if stale:
        notices.append({
            "kind": "info",
            "title": "No previous close",
            "body": (f"{_fmt_symlist(stale)} resolved a price but no prior session "
                     f"to measure it against; excluded from today's change."),
        })

    # A holding priced from a session that has already settled is not wrong,
    # but it is not today either — and mixing settled prices with live ones is
    # what made today's change move between refreshes. Say so.
    if 'PRICE ASOF' in df.columns:
        _today = datetime.now().date()
        settled = df.loc[df['PRICE ASOF'].apply(
            lambda d: d is not None and not pd.isna(d) and d < _today), 'SYMBOL'].tolist()
        if settled:
            notices.append({
                "kind": "warning",
                "title": "Priced from a settled session",
                "body": (f"{_fmt_symlist(settled)} could not be priced live and carry "
                         f"the last settled close. Today's change for these is zero "
                         f"by construction, not a reading of no movement."),
            })

    # The basis is a portfolio-level aggregate: if it comes from more than one
    # place the total is only as consistent as the mix, so name the mix.
    if 'PRICE SOURCE' in df.columns:
        mix = df['PRICE SOURCE'].value_counts().to_dict()
        primary = "yahoo:quote"
        if mix and set(mix) != {primary}:
            summary = " · ".join(f"{k or 'unpriced'} {v}" for k, v in mix.items())
            notices.append({
                "kind": "info",
                "title": "Mixed price sources",
                "body": (f"{summary}. The previous-close basis is reconciled to "
                         f"exchange settlement, so today's change is comparable "
                         f"across sources; the prices themselves are not all live."),
            })
    return notices


def main() -> None:
    """Main application entry point."""
    st.set_page_config(
        page_title="SAMHITA | Portfolio Intelligence",
        page_icon="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCAyNCAyNCI+PGNpcmNsZSBjeD0iMTIiIGN5PSIxMiIgcj0iMTAiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzRDN0RGMCIgc3Ryb2tlLXdpZHRoPSIyIi8+PHBhdGggZD0iTTggMTRsMy01IDIgMyAzLTQiIGZpbGw9Im5vbmUiIHN0cm9rZT0iIzRDN0RGMCIgc3Ryb2tlLXdpZHRoPSIyIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz48L3N2Zz4=",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # ─── Resolve the appearance BEFORE anything is styled ──────────────────
    # This must run FIRST. `theme` is written by the appearance control, which
    # lives deep in the rail — i.e. AFTER this point in the script. On the rerun
    # following a click, inject_css() would otherwise still see the PREVIOUS
    # appearance while every chart, which resolves its palette at render time
    # further down, already saw the new one: a page whose chrome and whose plots
    # disagree about which theme is active. Reading the DURABLE choice here,
    # first, makes the whole run — CSS, charts, tables, iframes — agree on one
    # value.
    st.session_state["theme"] = "light" if theme_choice() == "Paper" else "dark"
    inject_css(theme=st.session_state["theme"])
    st.session_state.setdefault("active_scope", "PORTFOLIO")

    # Single main-area progress slot, created UP FRONT (outside the rail) so the
    # same themed bar drives the entire run — quote resolution, analytics, and
    # the analysis history fetch — rather than one bar handing off to a second
    # further down the page with a gap between them. Invisible until the first
    # progress_bar() call; cleared when the run ends.
    progress_slot = st.empty()

    # ─── The control rail ──────────────────────────────────────────────────
    # Everything GLOBAL lives here — what to do with the session, what to look
    # at, how the app looks. A control's position is the only reliable statement
    # of its scope, so page-local controls (the chart window) live on the panel
    # they change, never here.
    #
    # Rail order is by frequency of use: View (every visit) → Session
    # (occasionally) → Anchor (rarely) → System (read-only) → Appearance
    # (almost never).
    with st.sidebar:
        # The mark, always at the very top. Streamlit pins its own page-nav to
        # the top of the sidebar and nothing emitted from Python can precede it
        # in the DOM, so the brand is lifted above it by CSS.
        render_nav_brand()

        st.markdown('<div class="sidebar-title">Session</div>', unsafe_allow_html=True)
        if st.button("Refresh Prices", width="stretch",
                     help="Clear cached quotes and re-walk the source hierarchy"):
            st.cache_data.clear()
            # Re-arm the progress cards: the next run is a real (slow) cache
            # miss, so show loading feedback for both surfaces.
            st.session_state.pop('_samhita_dash_loaded', None)
            st.session_state.pop('_samhita_an_key', None)
            st.toast("Price cache cleared")
            st.rerun()

        st.markdown('<div class="sidebar-title">Anchor Date</div>', unsafe_allow_html=True)
        render_control_hint("Custom start date · analysis metrics only")
        use_anchor = st.toggle("Enable Anchor Date", value=False, key="use_anchor_date")
        anchor_date = None
        if use_anchor:
            anchor_date = st.date_input(
                "Investment Start Date",
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now().date(),
                min_value=datetime(2010, 1, 1).date(),
                label_visibility="collapsed",
            )

        st.markdown('<div class="sidebar-title">System</div>', unsafe_allow_html=True)
        render_rail_readout([
            ("Version", VERSION, ""),
            ("Sources", "4-tier", "accent"),
            ("Cache", "5 min", ""),
        ])

        _render_appearance_control()

    # Load data
    df = load_data()
    if df is None:
        render_empty_state(
            "No portfolio file found",
            "Samhita reads its holdings from <strong>Summary Report.xlsx</strong> "
            "in the application folder. The file must carry ASSET NAME, SYMBOL, "
            "QUANTITY and AVERAGE PRICE — prices are resolved live and are not "
            "part of it.",
            eyebrow="Cold start",
            action_label="Add Summary Report.xlsx, then use Refresh Prices",
        )
        _render_footer()
        return

    required_columns = ['ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE']
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        render_empty_state(
            "Portfolio file is missing columns",
            f"<strong>Summary Report.xlsx</strong> must carry "
            f"{', '.join(required_columns)}. Not found: "
            f"<strong>{', '.join(missing_cols)}</strong>. "
            f"CURRENT PRICE is resolved live and is not required in the file.",
            eyebrow="Cold start",
            action_label="Add the columns, then use Refresh Prices",
        )
        _render_footer()
        return

    # Themed progress card — shown on the first load of the session; prices are
    # cached afterwards, so cosmetic reruns stay instant and quiet.
    _show_prog = not st.session_state.get('_samhita_dash_loaded', False)

    def _dash_progress(pct: int, label: str, sub: str = "") -> None:
        if _show_prog:
            progress_bar(progress_slot, pct, label, sub)

    df, metrics = calculate_metrics(df, progress=_dash_progress)

    if _show_prog:
        progress_bar(progress_slot, 100, "Portfolio Ready",
                     f"{len(df)} holdings · prices live")
        progress_slot.empty()
        st.session_state['_samhita_dash_loaded'] = True

    # ─── The page shell, identical on every page ───────────────────────────
    # Order is fixed and means something: the TAPE (what moved) sits above the
    # COMMAND BAR (what the portfolio is worth), which sits above the NOTICE
    # RAIL (the caveats on that), and the KPI strip answers "what changed since
    # I last looked" in one saccade before any page's own content begins.
    def _shell() -> None:
        # ─── The tape ──────────────────────────────────────────────────────────
        # The one element in the app that moves, because a tape is a thing that
        # moves. Fed from the quotes this run already resolved, so it cannot
        # disagree with the numbers below it.
        render_ticker(zip(df['SYMBOL'], df['CURRENT PRICE'], df['TODAY %']))

        # ─── The command bar ───────────────────────────────────────────────────
        # Reading order left to right is identity → value → trust: whose portfolio,
        # what it is worth, and whether the data behind that is current. Nothing
        # renders above this bar.
        _priced = int(df['FETCHED PRICE'].notna().sum())
        _n = len(df)
        if _priced == _n:
            _status, _tone = "LIVE", "success"
        elif _priced == 0:
            _status, _tone = "NO QUOTES", "danger"
        else:
            _status, _tone = f"PARTIAL {_priced}/{_n}", "warning"
        render_top_bar(
            target="PORTFOLIO",
            price=float(metrics['Total Current Value']),
            change_pct=float(metrics['Today Return %']),
            status_label=_status,
            status_tone=_tone,
            meta_items=[
                ("Holdings", f"{_n}"),
                ("As of", datetime.now().strftime("%d %b %Y · %H:%M")),
            ],
        )
        render_notice_rail(_quote_notices(df))

        # ─── The headline readings ─────────────────────────────────────────────
        # A KPI strip, not a row of columns: it caps row width so the cards never
        # squeeze past legibility and wraps to a second row instead.
        _gain = float(metrics['Total Gain'])
        _ret = float(metrics['Portfolio Return %'])
        _today = float(metrics['Today Return %'])
        _today_chg = float(metrics['Today Change'])
        render_kpi_strip([
            dict(label="Portfolio Value", value=format_currency(metrics['Total Current Value']),
                 subtext=f"Invested {format_currency(metrics['Total Invested'])}",
                 color_class="neutral", icon="briefcase"),
            dict(label="Absolute Gain", value=f"{'+' if _gain > 0 else ''}{format_currency(_gain)}",
                 subtext="Since inception", icon="trending",
                 color_class="success" if _gain >= 0 else "danger"),
            dict(label="Total Return", value=f"{'+' if _ret > 0 else ''}{_ret:.2f}%",
                 subtext="Against cost basis", icon="target",
                 color_class="success" if _ret >= 0 else "danger"),
            dict(label="Today", value=f"{'+' if _today > 0 else ''}{_today:.2f}%",
                 subtext=f"{'+' if _today_chg > 0 else ''}{format_currency(_today_chg)}",
                 icon="activity",
                 color_class="success" if _today >= 0 else "danger"),
            dict(label="Concentration", value=f"{metrics['Top 5 Concentration']:.1f}%",
                 subtext="Top 5 holdings", icon="layers",
                 color_class="warning" if metrics['Top 5 Concentration'] > 50 else "neutral"),
        ], max_cols=5, key="kpi-portfolio")

    def _safe_render(name: str, render_fn) -> None:
        """Render a page's content, and keep the shell if it fails.

        A page that raises must not take the command bar down with it — the
        reader still needs to see what the portfolio is worth and that the
        failure is in one view, not in the data.
        """
        try:
            render_fn()
        except Exception as exc:   # noqa: BLE001 — a page must not kill the app
            render_empty_state(
                f"{name} could not be rendered",
                f"<strong>{type(exc).__name__}</strong>: {_html.escape(str(exc))}",
                eyebrow="Page error",
                action_label="Try Refresh Prices, or switch view",
            )

    def _page_dashboard() -> None:
        _shell()
        _safe_render("Dashboard", lambda: _render_dashboard(df, metrics))

    def _page_analytics() -> None:
        _shell()
        _safe_render("Analytics", lambda: render_analysis_mode(
            df, metrics, anchor_date, progress_slot=progress_slot))

    # Real pages, not a radio. The rail's navigation is the app's own
    # structure — Streamlit pins it to the top of the sidebar and gives each
    # page a URL of its own, so a view can be linked to and returned to. A
    # radio posing as navigation gives up both and reads as a setting.
    st.navigation([
        st.Page(_page_dashboard, title="Dashboard",
                icon=":material/dashboard:", url_path="dashboard", default=True),
        st.Page(_page_analytics, title="Analytics",
                icon=":material/monitoring:", url_path="analytics"),
    ], position="sidebar").run()

    _render_footer()




def _render_dashboard(df: pd.DataFrame, metrics: dict) -> None:
    """The Dashboard page — holdings, movers, composition, concentration."""
    tab1, tab2, tab3 = st.tabs(["Performance Analysis", "Portfolio Details", "Holdings Analytics"])

    with tab1:
        # ── Performance Snapshot ────────────────────────────────────────
        render_section_header(
            "Performance Snapshot",
            "Aggregate position outcomes, measured against cost basis",
            icon="activity",
            accent="emerald",
        )

        total_gain = df['GAIN'].sum()
        total_invested = df['INVESTED'].sum()
        total_return_pct = (total_gain / total_invested * 100) if total_invested > 0 else 0

        winners = df[df['GAIN %'] > 0]
        losers = df[df['GAIN %'] < 0]
        n_winners = len(winners)
        n_losers = len(losers)
        n_total = len(df)

        avg_winner = winners['GAIN %'].mean() if n_winners > 0 else 0
        avg_loser = losers['GAIN %'].mean() if n_losers > 0 else 0

        best_performer = df.loc[df['GAIN %'].idxmax()]
        worst_performer = df.loc[df['GAIN %'].idxmin()]

        c1, c2, c3, c4, c5, c6 = st.columns(6)

        with c1:
            render_metric_card(
                "Total P&L",
                format_currency(total_gain),
                subtext=f"{total_return_pct:+.2f}% return",
                color_class="success" if total_gain >= 0 else "danger",
            )

        with c2:
            win_rate = (n_winners / n_total * 100) if n_total > 0 else 0
            cls = 'success' if win_rate > 50 else 'warning' if win_rate > 30 else 'danger'
            render_metric_card(
                "Win Rate",
                f"{win_rate:.0f}%",
                subtext=f"{n_winners}W · {n_losers}L",
                color_class=cls,
            )

        with c3:
            cls = 'success' if avg_winner > 0 else 'neutral' if n_winners == 0 else 'warning'
            render_metric_card(
                "Avg Winner",
                f"{avg_winner:+.1f}%",
                subtext=f"{n_winners} positions",
                color_class=cls,
            )

        with c4:
            cls = 'danger' if avg_loser < 0 else 'neutral' if n_losers == 0 else 'warning'
            render_metric_card(
                "Avg Loser",
                f"{avg_loser:.1f}%",
                subtext=f"{n_losers} positions",
                color_class=cls,
            )

        with c5:
            cls = 'success' if best_performer['GAIN %'] > 0 else 'danger' if best_performer['GAIN %'] < 0 else 'neutral'
            render_metric_card(
                "Best Performer",
                f"{best_performer['GAIN %']:+.1f}%",
                subtext=str(best_performer['SYMBOL']),
                color_class=cls,
            )

        with c6:
            cls = 'danger' if worst_performer['GAIN %'] < 0 else 'success' if worst_performer['GAIN %'] > 0 else 'neutral'
            render_metric_card(
                "Worst Performer",
                f"{worst_performer['GAIN %']:.1f}%",
                subtext=str(worst_performer['SYMBOL']),
                color_class=cls,
            )

        # ── Top Movers ──────────────────────────────────────────────────
        render_section_header(
            "Top Movers",
            "Best and worst five positions by return on cost",
            icon="trending",
            accent="cyan",
        )

        col_gainers, col_losers = st.columns(2)

        with col_gainers:
            top_5_gainers = df.nlargest(5, 'GAIN %')[['SYMBOL', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'GAIN']]
            fig_gainers = go.Figure()
            fig_gainers.add_trace(go.Bar(
                y=top_5_gainers['SYMBOL'][::-1],
                x=top_5_gainers['GAIN %'][::-1],
                orientation='h',
                marker_color=[chart_color("emerald") if v >= 0 else chart_color("rose")
                              for v in top_5_gainers['GAIN %'][::-1]],
                text=[f"{x:+.1f}%" for x in top_5_gainers['GAIN %'][::-1]],
                # OUTSIDE: `auto` drops the value inside the bar and paints it
                # in the app's ink — the same darkness as the saturated fill
                # it lands on, and rotated 90 degrees in a narrow column.
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=11, color=ink_muted(), family=CHART_FONT),
                hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Weight: %{customdata[0]:.1f}%<br>Contribution: %{customdata[1]:.2f}%<extra></extra>",
                customdata=top_5_gainers[['WT', 'WEIGHTED RETURN %']][::-1].values,
            ))
            _apply_theme(
                fig_gainers, height=CHART_HEIGHT_SM, show_legend=False,
                margin=CHART_MARGIN_BAR,
                title="Absolute Return %",
            )
            _pad_for_value_labels(fig_gainers)
            render_chart_panel(fig_gainers, key="top-gainers", title="Top Gainers",
                               context="best 5 by return on cost")

        with col_losers:
            top_5_losers = df.nsmallest(5, 'GAIN %')[['SYMBOL', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'GAIN']]
            fig_losers = go.Figure()
            fig_losers.add_trace(go.Bar(
                y=top_5_losers['SYMBOL'],
                x=top_5_losers['GAIN %'],
                orientation='h',
                marker_color=[chart_color("rose") if v < 0 else chart_color("emerald")
                              for v in top_5_losers['GAIN %']],
                text=[f"{x:+.1f}%" for x in top_5_losers['GAIN %']],
                # OUTSIDE: `auto` drops the value inside the bar and paints it
                # in the app's ink — the same darkness as the saturated fill
                # it lands on, and rotated 90 degrees in a narrow column.
                textposition='outside',
                cliponaxis=False,
                textfont=dict(size=11, color=ink_muted(), family=CHART_FONT),
                hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Weight: %{customdata[0]:.1f}%<br>Contribution: %{customdata[1]:.2f}%<extra></extra>",
                customdata=top_5_losers[['WT', 'WEIGHTED RETURN %']].values,
            ))
            _apply_theme(
                fig_losers, height=CHART_HEIGHT_SM, show_legend=False,
                margin=CHART_MARGIN_BAR,
                title="Absolute Return %",
            )
            _pad_for_value_labels(fig_losers)
            render_chart_panel(fig_losers, key="top-losers", title="Top Losers",
                               context="worst 5 by return on cost")

        # ── Risk-Return Profile ─────────────────────────────────────────
        render_section_header(
            "Risk-Return Profile",
            "Return on cost against portfolio weight · bubble area is current value",
            icon="crosshair",
            accent="violet",
        )

        max_val = df['CURR. VALUE'].max()
        bubble_sizes = (df['CURR. VALUE'] / max_val * 40) + 10

        # ── Which points get a printed label ────────────────────────────
        # Labelling all 32 put ~20 of them on top of each other: the middle
        # of this plot is where most holdings sit by construction (weights
        # cluster near the mean), so that is exactly where the labels
        # collide. Plotly has no collision avoidance, and an offset
        # computed here in data coordinates stops being right the moment
        # the reader zooms — so the fix is not to place labels more
        # cleverly but to print fewer of them.
        #
        # A label earns its place by being the answer to a question a
        # reader actually asks of this chart: what are my biggest
        # positions, and what are my best and worst performers. Everything
        # else keeps its identity on hover, so nothing is lost — a legible
        # eight beats an illegible thirty-two.
        _n_label = 4
        if len(df) <= 12:
            _labelled = set(df['SYMBOL'])          # no crowding to solve
        else:
            _labelled = (set(df.nlargest(_n_label, 'WT')['SYMBOL'])
                         | set(df.nlargest(_n_label, 'GAIN %')['SYMBOL'])
                         | set(df.nsmallest(_n_label, 'GAIN %')['SYMBOL']))
        _labels = [sym if sym in _labelled else "" for sym in df['SYMBOL']]

        # Which SIDE of its marker each printed label sits on. Starting
        # side is away from the crowded middle — above the median return
        # the label goes up, below it goes down — but two neighbours on the
        # same side still stack, which is what put AUTOIETF on top of
        # PSUBNKIETF (0.1pp apart in weight, 1pp in return). So the labels
        # are placed in x order and a label flips to the opposite side when
        # one already placed is close enough on BOTH axes to collide with
        # it. Deterministic from the data, so it does not move between
        # reruns, and it degrades to the simple rule when nothing is close.
        _mid_return = df['GAIN %'].median()
        _xr = max(float(df['WT'].max() - df['WT'].min()), 1e-9)
        _yr = max(float(df['GAIN %'].max() - df['GAIN %'].min()), 1e-9)
        _side_of: dict[str, str] = {}
        _placed: list[tuple[float, float, str]] = []
        _order = df.loc[df['SYMBOL'].isin(_labelled)].sort_values('WT')
        for _sym, _x, _y in zip(_order['SYMBOL'], _order['WT'], _order['GAIN %']):
            _side = 'top center' if _y >= _mid_return else 'bottom center'
            if any(abs(_x - _px) / _xr < 0.08 and abs(_y - _py) / _yr < 0.08
                   and _ps == _side for _px, _py, _ps in _placed):
                _side = 'bottom center' if _side == 'top center' else 'top center'
            _placed.append((float(_x), float(_y), _side))
            _side_of[_sym] = _side
        _positions = [_side_of.get(sym, 'top center') for sym in df['SYMBOL']]

        fig_scatter = go.Figure()
        fig_scatter.add_trace(go.Scatter(
            x=df['WT'],
            y=df['GAIN %'],
            mode='markers+text',
            marker=dict(
                size=bubble_sizes,
                color=df['GAIN %'],
                colorscale=[[0, chart_color("rose")], [0.5, chart_color("accent")], [1, chart_color("emerald")]],
                cmid=0,
                line=dict(width=1, color=panel_bg()),
                opacity=0.85,
            ),
            text=_labels,
            textposition=_positions,
            textfont=dict(size=9, color=ink(), family=CHART_FONT),
            # The symbol moves into customdata because `text` is now blank
            # for most points — hover must still name every one of them.
            hovertemplate=("<b>%{customdata[0]}</b><br>Weight: %{x:.1f}%"
                           "<br>Return: %{y:.2f}%<br>Value: \u20b9%{customdata[1]:,.0f}"
                           "<extra></extra>"),
            customdata=df[['SYMBOL', 'CURR. VALUE']].values,
        ))

        fig_scatter.add_hline(y=0, line_dash="dash", line_color=ink_subtle(), line_width=1)
        avg_weight = df['WT'].mean()
        fig_scatter.add_vline(
            x=avg_weight, line_dash="dash", line_color=ink_subtle(), line_width=1,
            annotation_text=f"Avg Wt: {avg_weight:.1f}%", annotation_position="top",
        )

        _apply_theme(
            fig_scatter, height=CHART_HEIGHT_LG, show_legend=False,
            margin=CHART_MARGIN,
            title="Weight vs Return Matrix",
            x_title="Portfolio Weight (%)",
            y_title="Gain/Loss (%)",
        )
        render_chart_panel(fig_scatter, key="risk-return", units="weight vs return")
        render_note("Labels mark the largest positions and the best and worst "
                    "performers. Hover names any point.")

        # ── Return Attribution ──────────────────────────────────────────
        render_section_header(
            "Return Attribution",
            "Each holding's share of the portfolio return, weighted by cost",
            icon="bar-chart",
            accent="violet",
        )

        contrib_sorted = df.sort_values('WEIGHTED RETURN %', ascending=False).copy()
        fig_waterfall = go.Figure()
        colors = [chart_color("emerald") if x >= 0 else chart_color("rose") for x in contrib_sorted['WEIGHTED RETURN %']]
        fig_waterfall.add_trace(go.Bar(
            x=contrib_sorted['SYMBOL'],
            y=contrib_sorted['WEIGHTED RETURN %'],
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in contrib_sorted['WEIGHTED RETURN %']],
            # OUTSIDE, and horizontal. `auto` lets Plotly drop the label inside
            # the bar whenever it "fits", and in a 37px-wide column that means
            # rotating it 90 degrees — so every value read bottom-to-top in the
            # app's ink ON a saturated fill of the same darkness. A value label
            # belongs on the panel surface, where the ink it is drawn in is the
            # ink that surface was contrast-checked against.
            textposition='outside',
            textangle=0,
            # Let the tallest bar's label draw into the margin instead of being
            # clipped at the axis.
            cliponaxis=False,
            textfont=dict(size=9, color=ink_muted(), family=CHART_FONT),
            hovertemplate="<b>%{x}</b><br>Contribution: %{y:.3f}%<br>Return: %{customdata[0]:.1f}%<br>Weight: %{customdata[1]:.1f}%<extra></extra>",
            customdata=contrib_sorted[['GAIN %', 'WT']].values,
        ))
        _apply_theme(
            fig_waterfall, height=CHART_HEIGHT_LG, show_legend=False,
            # Extra headroom: the outside label on the tallest bar needs
            # somewhere to sit that is not the panel's edge.
            margin={**CHART_MARGIN_ROTATED, "t": 30},
            title="Weighted Return Contribution · sorted by impact",
            y_title="Contribution (%)",
        )
        fig_waterfall.update_xaxes(tickangle=45)
        # Vertical bars: the labels sit above (or below) the bar ends.
        _pad_for_value_labels(fig_waterfall, horizontal=False, frac=0.12)
        # The values are PERCENTAGE POINTS of the portfolio's return, not
        # rupees — the panel said "₹ contribution" over a "%"-titled axis.
        render_chart_panel(fig_waterfall, key="gain-waterfall",
                           units="pp of portfolio return")

        # ── Portfolio Composition ───────────────────────────────────────
        render_section_header(
            "Portfolio Composition",
            "Market value by holding · colour is return on cost",
            icon="cube",
            accent="cyan",
        )

        fig_treemap = px.treemap(
            df, path=['SYMBOL'], values='CURR. VALUE', color='GAIN %',
            **_gain_colorscale(df['GAIN %']),
        )
        _style_treemap(fig_treemap, height=CHART_HEIGHT_LG)
        render_chart_panel(fig_treemap, key="allocation-map",
                           units="market value · colour = gain %")

    with tab2:
        render_section_header(
            "Portfolio Holdings",
            "Every position, priced live through the source hierarchy",
            icon="database",
            accent="accent",
        )

        # The holdings table goes through the app's ONE table primitive.
        # It was previously a `DataFrame.to_html()` string with per-cell
        # inline colours — which meant it carried its own typeface, row
        # height and hover, and its gain colours were hardcoded hexes that
        # could not follow the appearance switch. `render_table_panel`
        # gives it the same header anatomy as every chart on the page, and
        # `sign_color_cols` does the gain/loss tinting from the theme.
        holdings = df[['SYMBOL', 'ASSET NAME', 'QUANTITY', 'AVERAGE PRICE',
                       'CURRENT PRICE', 'INVESTED', 'CURR. VALUE',
                       'GAIN', 'GAIN %', 'TODAY %', 'WT']].copy()
        holdings = holdings.sort_values('CURR. VALUE', ascending=False)
        holdings.insert(0, 'RANK', range(1, len(holdings) + 1))

        render_table_panel(
            holdings, key="holdings",
            context=f"{len(holdings)} holdings · live prices",
            meta=datetime.now().strftime("%d %b %Y · %H:%M"),
            chip=("LIVE", "success") if df['FETCHED PRICE'].notna().all()
                 else ("PARTIAL", "warning"),
            label_col='SYMBOL',
            show_index=False,
            sign_color_cols={'GAIN', 'GAIN %', 'TODAY %'},
            col_precision={'QUANTITY': 0, 'AVERAGE PRICE': 2, 'CURRENT PRICE': 2,
                           'INVESTED': 0, 'CURR. VALUE': 0, 'GAIN': 0,
                           'GAIN %': 2, 'TODAY %': 2, 'WT': 2, 'RANK': 0},
            col_labels={'CURR. VALUE': 'Value', 'AVERAGE PRICE': 'Avg Cost',
                        'CURRENT PRICE': 'Price', 'GAIN %': 'Gain %',
                        'TODAY %': 'Today %', 'WT': 'Weight %'},
            max_height=560,
        )
        render_note("Amounts in rupees. Gain is against cost basis; "
                    "Today % is against the previous session's close.")

        excel_data = to_excel(df)
        st.download_button(
            "Export Raw Portfolio Data (Excel)",
            excel_data,
            file_name=f"Samhita_portfolio_details_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheet.sheet",
        )
    
    with tab3:
        n_holdings = len(df)
        weights = df['WT'].values / 100

        hhi = (df['WT'] ** 2).sum()
        effective_n = 10000 / hhi if hhi > 0 else n_holdings
        gini = 0
        if n_holdings > 1:
            sorted_weights = np.sort(weights)
            cum_weights = np.cumsum(sorted_weights)
            gini = 1 - 2 * np.sum(cum_weights) / (n_holdings * cum_weights[-1]) if cum_weights[-1] > 0 else 0

        avg_weight = weights.mean()
        div_ratio = 1 / (hhi / 10000) if hhi > 0 else n_holdings

        render_section_header(
            "Concentration Metrics",
            "How much of the portfolio sits in how few names",
            icon="layers", accent="cyan",
        )
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        with c1:
            render_metric_card("Holdings", f"{n_holdings}", subtext="Unique positions",
                               color_class="warning")
        with c2:
            top5 = metrics['Top 5 Concentration']
            render_metric_card("Top 5", f"{top5:.1f}%", subtext="Concentration",
                               color_class='warning' if top5 > 60 else 'success')
        with c3:
            top10 = df['WT'].nlargest(10).sum()
            render_metric_card("Top 10", f"{top10:.1f}%", subtext="Concentration",
                               color_class='warning' if top10 > 80 else 'success')
        with c4:
            render_metric_card("Effective N", f"{effective_n:.1f}",
                               subtext="1/HHI equivalent", color_class="info")
        with c5:
            render_metric_card("HHI", f"{hhi:.0f}", subtext="<1500 = diverse",
                               color_class='warning' if hhi > 1500 else 'success')
        with c6:
            render_metric_card("Gini Coeff", f"{gini:.2f}",
                               subtext="0 = equal · 1 = concentrated",
                               color_class="neutral")

        render_section_header(
            "Performance Distribution",
            "How returns are spread across positions, and how weight is spread with them",
            icon="bar-chart", accent="emerald",
        )
        c1, c2, c3, c4, c5, c6 = st.columns(6)

        profitable = (df['GAIN %'] > 0).sum()
        losing = (df['GAIN %'] < 0).sum()
        win_rate = profitable / n_holdings * 100 if n_holdings > 0 else 0

        with c1:
            render_metric_card("Winners", f"{profitable}", subtext="Profitable",
                               color_class="success")
        with c2:
            render_metric_card("Losers", f"{losing}", subtext="Underwater",
                               color_class="danger")
        with c3:
            cls = 'success' if win_rate > 60 else 'warning' if win_rate > 40 else 'danger'
            render_metric_card("Win Rate", f"{win_rate:.0f}%", subtext="Batting avg",
                               color_class=cls)
        with c4:
            avg_gain = df['GAIN %'].mean()
            render_metric_card("Avg Return", f"{avg_gain:+.1f}%", subtext="Mean gain",
                               color_class='success' if avg_gain > 0 else 'danger')
        with c5:
            median_gain = df['GAIN %'].median()
            render_metric_card("Median Return", f"{median_gain:+.1f}%",
                               subtext="50th percentile",
                               color_class='success' if median_gain > 0 else 'danger')
        with c6:
            gain_std = df['GAIN %'].std()
            render_metric_card("Return Dispersion", f"{gain_std:.1f}%",
                               subtext="Std deviation", color_class="warning")


        col_pie, col_lorenz = st.columns(2)

        with col_pie:
            fig_tree = px.treemap(
                df, path=['SYMBOL'], values='WT', color='GAIN %',
                **_gain_colorscale(df['GAIN %']),
            )
            _style_treemap(fig_tree, height=CHART_HEIGHT_MD)
            render_chart_panel(fig_tree, key="allocation-tree",
                               title="Weight Distribution",
                               context="share of value · colour = gain %")

        with col_lorenz:
            sorted_weights = np.sort(df['WT'].values)[::-1]
            cum_weights = np.cumsum(sorted_weights)
            n = len(sorted_weights)

            fig_lorenz = go.Figure()
            fig_lorenz.add_trace(go.Scatter(
                x=list(range(n + 1)),
                y=[0] + list(np.linspace(0, 100, n)),
                mode='lines',
                name='Equal Weight',
                line=dict(color=ink_subtle(), dash='dash', width=1),
            ))
            fig_lorenz.add_trace(go.Scatter(
                x=list(range(n + 1)),
                y=[0] + list(cum_weights),
                mode='lines+markers',
                name='Portfolio',
                line=dict(color=chart_color("accent"), width=2),
                marker=dict(size=4),
                fill='tonexty',
                fillcolor=chart_rgba("accent", 0.15),
            ))
            fig_lorenz.add_hline(y=50, line_dash="dot", line_color=chart_color("emerald"),
                                annotation_text="50%", annotation_position="right")
            fig_lorenz.add_hline(y=80, line_dash="dot", line_color=chart_color("cyan"),
                                annotation_text="80%", annotation_position="right")
            _apply_theme(
                fig_lorenz, height=CHART_HEIGHT_MD, show_legend=True,
                margin=CHART_MARGIN,
                title="Lorenz Curve · cumulative %",
                x_title='# Holdings (ranked)',
                y_title='Cumulative Weight (%)',
            )
            fig_lorenz.update_yaxes(range=[0, 105])
            render_chart_panel(fig_lorenz, key="lorenz",
                               title="Concentration Curve",
                               context="cumulative weight vs holdings")


        render_section_header(
            "Risk & Return Contribution",
            "What each holding adds to return, beside what it adds to concentration",
            icon="shield", accent="rose",
        )

        contrib_df = df[['SYMBOL', 'ASSET NAME', 'WT', 'GAIN %', 'WEIGHTED RETURN %']].copy()
        contrib_df['Weight'] = contrib_df['WT'].apply(lambda x: f"{x:.2f}%")
        contrib_df['Return'] = contrib_df['GAIN %'].apply(lambda x: f"{x:+.2f}%")
        contrib_df['Contribution'] = contrib_df['WEIGHTED RETURN %'].apply(lambda x: f"{x:+.3f}%")
        contrib_df['Risk Weight'] = (contrib_df['WT'] ** 2) / hhi * 100
        contrib_df['Risk Contrib'] = contrib_df['Risk Weight'].apply(lambda x: f"{x:.1f}%")
        contrib_df = contrib_df.sort_values('WEIGHTED RETURN %', ascending=False)

        fig_contrib = make_subplots(rows=1, cols=2, shared_yaxes=True,
                                    subplot_titles=('Return Contribution', 'Risk Contribution'),
                                    # Room for the left panel's outside value
                                    # labels, which at 0.02 landed inside the
                                    # right panel.
                                    horizontal_spacing=0.10)
        # Plotly draws subplot titles in ITS default 16px sans. These name
        # two columns of a chart, which is the app's caption tier.
        for _ann in fig_contrib.layout.annotations:
            _ann.font = dict(size=10, family="JetBrains Mono, monospace",
                             color=ink_subtle())

        colors_ret = [chart_color("emerald") if x >= 0 else chart_color("rose") for x in contrib_df['WEIGHTED RETURN %']]

        fig_contrib.add_trace(go.Bar(
            y=contrib_df['SYMBOL'],
            x=contrib_df['WEIGHTED RETURN %'],
            orientation='h',
            marker_color=colors_ret,
            text=[f"{x:.2f}%" for x in contrib_df['WEIGHTED RETURN %']],
            # OUTSIDE: `auto` drops the value inside the bar and paints it
            # in the app's ink — the same darkness as the saturated fill
            # it lands on, and rotated 90 degrees in a narrow column.
            textposition='outside',
            cliponaxis=False,
            textfont=dict(size=9, color=ink_muted(), family=CHART_FONT),
            showlegend=False,
        ), row=1, col=1)

        fig_contrib.add_trace(go.Bar(
            y=contrib_df['SYMBOL'],
            x=contrib_df['Risk Weight'],
            orientation='h',
            marker_color=chart_color("accent"),
            text=[f"{x:.1f}%" for x in contrib_df['Risk Weight']],
            # OUTSIDE: `auto` drops the value inside the bar and paints it
            # in the app's ink — the same darkness as the saturated fill
            # it lands on, and rotated 90 degrees in a narrow column.
            textposition='outside',
            cliponaxis=False,
            textfont=dict(size=9, color=ink_muted(), family=CHART_FONT),
            showlegend=False,
        ), row=1, col=2)

        # Through the shared grammar, not a hand-rolled copy of it: the
        # crosshair, zero line, tick face and hover precision all come from
        # style_axes, so this pair of bar panels reads as the same object
        # as every other chart on the page.
        _apply_theme(fig_contrib, height=max(CHART_HEIGHT_MD, n_holdings * 22 + 80),
                     margin=CHART_MARGIN_BAR)
        # A horizontal bar's categories are the SYMBOLS; a grid across them
        # is a line between every pair of names and says nothing.
        fig_contrib.update_yaxes(showgrid=False, zeroline=False)
        _pad_for_value_labels(fig_contrib)

        render_chart_panel(fig_contrib, key="contribution",
                               units="return pp · risk share %")
        
        # Statistics as READOUTS, not markdown bullets. A bullet list is
        # prose; these are figures, and figures belong in the app's
        # tabular-numeral rail readout where a changed value is SEEN
        # rather than read. Right-aligned and monospaced, so the four
        # columns share one baseline grid.
        with st.expander("Detailed Statistics", expanded=False):
            col_s1, col_s2, col_s3, col_s4 = st.columns(4)
            with col_s1:
                render_sub_header("Weight")
                render_rail_readout([
                    ("Mean", f"{df['WT'].mean():.2f}%", ""),
                    ("Median", f"{df['WT'].median():.2f}%", ""),
                    ("Std", f"{df['WT'].std():.2f}%", ""),
                    ("Max", f"{df['WT'].max():.2f}%", "accent"),
                    ("Min", f"{df['WT'].min():.2f}%", ""),
                ])
            with col_s2:
                render_sub_header("Return")
                _gp = df['GAIN %']
                render_rail_readout([
                    ("Mean", f"{_gp.mean():.2f}%", "long" if _gp.mean() >= 0 else "short"),
                    ("Median", f"{_gp.median():.2f}%", "long" if _gp.median() >= 0 else "short"),
                    ("Std", f"{_gp.std():.2f}%", ""),
                    ("Max", f"{_gp.max():.2f}%", "long"),
                    ("Min", f"{_gp.min():.2f}%", "short"),
                ])
            with col_s3:
                render_sub_header("Concentration")
                render_rail_readout([
                    ("Top 1", f"{df['WT'].max():.1f}%", ""),
                    ("Top 3", f"{df['WT'].nlargest(3).sum():.1f}%", ""),
                    ("Top 5", f"{df['WT'].nlargest(5).sum():.1f}%",
                     "caution" if df['WT'].nlargest(5).sum() > 50 else ""),
                    ("Top 10", f"{df['WT'].nlargest(10).sum():.1f}%", ""),
                    ("Bottom 50%", f"{df['WT'].nsmallest(n_holdings//2).sum():.1f}%", ""),
                ])
            with col_s4:
                render_sub_header("Diversification")
                render_rail_readout([
                    ("HHI", f"{hhi:.0f}", ""),
                    ("Effective N", f"{effective_n:.1f}", "accent"),
                    ("Gini", f"{gini:.3f}", ""),
                    ("Div Ratio", f"{div_ratio:.2f}", ""),
                    ("Entropy", f"{-np.sum(weights * np.log(weights + 1e-10)):.2f}", ""),
                ])


# =========================================================================
# ANALYSIS MODE - INSTITUTIONAL GRADE ANALYTICS
# =========================================================================

# Annual risk-free rate used by every risk-adjusted metric (Sharpe, Sortino,
# alpha, Treynor). Defined once so the cards and the rolling charts agree.
RF_RATE = 0.065

BENCHMARK_TICKER = '^NSEI'  # NIFTY 50 only
BENCHMARK_NAME = 'NIFTY 50'


@st.cache_data(ttl=300, show_spinner=False)
def fetch_analysis_data(
    symbols: list[str], days_back: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch historical data for portfolio and NIFTY 50 benchmark.
    Portfolio data is aligned to NIFTY 50 trading dates to avoid
    holiday/timezone edge cases.

    Diagnostics go to the terminal log; no Streamlit spinner/banners here.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)

    log.section("SAMHITA · ANALYSIS HISTORY")
    log.step(f"PRIMARY · yfinance · {len(symbols)} holding(s) + benchmark "
             f"({start_date:%d-%b-%Y} → {end_date:%d-%b-%Y})")
    t0 = time.perf_counter()

    try:
        # First fetch NIFTY 50 to get valid trading dates
        benchmark_data = yf.download(
            tickers=BENCHMARK_TICKER,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d',
            progress=False,
            auto_adjust=False
        )
        
        if benchmark_data.empty:
            log.error("Benchmark (NIFTY 50) returned empty data")
            log.line("═", 70)
            return pd.DataFrame(), pd.DataFrame()

        # Get NIFTY 50 close prices
        benchmark_close = benchmark_data['Close']
        if isinstance(benchmark_close, pd.DataFrame):
            benchmark_close = benchmark_close.iloc[:, 0]
        benchmark_df = benchmark_close.to_frame(name=BENCHMARK_NAME)
        
        # Get valid trading dates from NIFTY 50
        valid_dates = benchmark_df.index
        
        # Now fetch portfolio holdings (.NS fallback; '.'-qualified symbols used as-is)
        ticker_map = {_to_yf_ticker(s): s for s in symbols}
        tickers = list(ticker_map.keys())

        portfolio_data = yf.download(
            tickers=tickers,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d',
            progress=False,
            threads=True,
            auto_adjust=False
        )
        
        if portfolio_data.empty:
            log.warning(f"Benchmark OK ({len(benchmark_df)} rows) but portfolio data empty")
            log.line("═", 70)
            return pd.DataFrame(), benchmark_df

        # Get close prices
        if len(tickers) == 1:
            portfolio_close = portfolio_data['Close'].to_frame()
            portfolio_close.columns = [symbols[0]]
        else:
            portfolio_close = portfolio_data['Close']
            portfolio_close.columns = [ticker_map.get(c, c) for c in portfolio_close.columns]
        
        # Align portfolio data to NIFTY 50 dates only
        portfolio_aligned = portfolio_close.reindex(valid_dates)
        
        # Forward fill any missing values (in case some stocks didn't trade)
        portfolio_aligned = portfolio_aligned.ffill()

        dt = time.perf_counter() - t0
        log.success(
            f"History loaded · {len(portfolio_aligned.columns)} holdings × "
            f"{len(portfolio_aligned)} rows · benchmark {len(benchmark_df)} rows in {dt:.1f}s"
        )
        log.line("═", 70)
        return portfolio_aligned, benchmark_df

    except Exception as e:
        log.error(f"Analysis history fetch failed: {type(e).__name__}: {e}")
        log.line("═", 70)
        return pd.DataFrame(), pd.DataFrame()


def compute_metrics(
    returns: pd.Series,
    benchmark_returns: pd.Series | None = None,
    rf_rate: float = RF_RATE,
) -> dict[str, Any]:
    """Compute institutional-grade performance metrics.

    Handles edge cases:
    - Short periods (< 5 days)
    - Negative total returns
    - Zero volatility
    - Missing benchmark data
    """
    m = {}
    
    if returns.empty or len(returns) < 2:
        # Return empty dict with safe defaults
        return {
            'total_return': 0, 'cagr': 0, 'volatility': 0, 'daily_vol': 0,
            'periods': 0, 'annualised': False,
            'max_drawdown': 0, 'drawdown_series': pd.Series(),
            'sharpe': 0, 'sortino': 0, 'calmar': 0,
            'var_95': 0, 'var_99': 0, 'cvar_95': 0,
            'win_rate': 0, 'win_days': 0, 'lose_days': 0,
            'best_day': 0, 'worst_day': 0,
            'skewness': 0, 'kurtosis': 0, 'profit_factor': 0,
            'beta': 1, 'alpha': 0, 'correlation': 0, 'r_squared': 0,
            'tracking_error': 0, 'info_ratio': 0, 'treynor': 0,
            'up_capture': 100, 'down_capture': 100, 'benchmark_return': 0
        }
    
    # Period metrics
    total_ret = (1 + returns).prod() - 1
    n_days = len(returns)
    
    m['total_return'] = total_ret * 100

    # Annualised return — ONE formula for every window length. The old code
    # forced the exponent to 1 below 252 days (so a 3-month return was reported
    # unannualised) while simple-scaling below 20 days, which put a cliff at
    # exactly n=20 where CAGR jumped by an order of magnitude. Geometric
    # annualisation is continuous across every window; `annualised` tells the
    # UI when the window is too short for the figure to mean much.
    m['periods'] = n_days
    m['annualised'] = n_days >= 20
    if total_ret > -1:  # anything but a total loss
        m['cagr'] = ((1 + total_ret) ** (252 / n_days) - 1) * 100
    else:
        m['cagr'] = -100  # Total loss
    
    # Volatility
    daily_vol = returns.std()
    m['volatility'] = daily_vol * np.sqrt(252) * 100 if daily_vol > 0 else 0
    m['daily_vol'] = daily_vol * 100
    
    # Drawdown
    cum = (1 + returns).cumprod()
    # The starting value (1.0) is itself a peak candidate, so a portfolio that
    # falls from day one still registers the drawdown from its opening level.
    peak = cum.expanding().max().clip(lower=1.0)
    dd = (cum - peak) / peak
    m['max_drawdown'] = dd.min() * 100
    m['drawdown_series'] = dd * 100
    
    # Risk-adjusted ratios
    rf_daily = rf_rate / 252
    excess = returns - rf_daily
    excess_mean = excess.mean()
    
    # Sharpe - handle zero/near-zero volatility
    if daily_vol > 1e-8:
        m['sharpe'] = (excess_mean / daily_vol) * np.sqrt(252)
    else:
        m['sharpe'] = 0 if abs(excess_mean) < 1e-8 else (np.sign(excess_mean) * 10)  # Cap at ±10
    
    # Sortino — downside deviation is the root-mean-square SHORTFALL below the
    # target, taken across every observation. The std() of just the negative
    # subset measures spread around the mean loss, which is a different (and
    # smaller) quantity that flatters the ratio.
    shortfall = np.minimum(returns - rf_daily, 0.0)
    downside_vol = float(np.sqrt((shortfall ** 2).mean()))
    if downside_vol > 1e-8:
        m['sortino'] = (excess_mean / downside_vol) * np.sqrt(252)
    else:
        # Never fell short of the target over this window.
        m['sortino'] = m['sharpe'] * 1.5 if m['sharpe'] > 0 else 0
    
    # Calmar - handle zero drawdown
    if abs(m['max_drawdown']) > 0.01:  # At least 0.01% drawdown
        m['calmar'] = m['cagr'] / abs(m['max_drawdown'])
    else:
        m['calmar'] = m['cagr'] if m['cagr'] > 0 else 0
    
    # VaR and CVaR (always negative or zero for losses)
    m['var_95'] = np.percentile(returns, 5) * 100
    m['var_99'] = np.percentile(returns, 1) * 100
    var_threshold = np.percentile(returns, 5)
    tail = returns[returns <= var_threshold]
    m['cvar_95'] = tail.mean() * 100 if len(tail) > 0 else m['var_95']
    
    # Win rate
    m['win_rate'] = (returns > 0).mean() * 100
    m['win_days'] = int((returns > 0).sum())
    m['lose_days'] = int((returns < 0).sum())
    
    # Best/Worst
    m['best_day'] = returns.max() * 100
    m['worst_day'] = returns.min() * 100
    
    # Skew and Kurtosis - need enough data
    if n_days >= 5:
        m['skewness'] = returns.skew()
        m['kurtosis'] = returns.kurtosis()
    else:
        m['skewness'] = 0
        m['kurtosis'] = 0
    
    # Profit Factor
    gains = returns[returns > 0].sum()
    losses = abs(returns[returns < 0].sum())
    if losses > 1e-8:
        m['profit_factor'] = gains / losses
    elif gains > 0:
        m['profit_factor'] = 10  # Cap at 10 for display
    else:
        m['profit_factor'] = 0
    
    # Initialize benchmark defaults
    m['beta'] = 1
    m['alpha'] = 0
    m['correlation'] = 0
    m['r_squared'] = 0
    m['tracking_error'] = 0
    m['info_ratio'] = 0
    m['treynor'] = 0
    m['up_capture'] = 100
    m['down_capture'] = 100
    m['benchmark_return'] = 0
    
    # Benchmark-relative metrics
    if benchmark_returns is not None and len(benchmark_returns) > 5:
        aligned = pd.concat([returns, benchmark_returns], axis=1).dropna()
        if len(aligned) > 5:
            p_ret = aligned.iloc[:, 0]
            b_ret = aligned.iloc[:, 1]
            
            # Beta
            var_b = b_ret.var()
            if var_b > 1e-10:
                cov = np.cov(p_ret, b_ret)[0, 1]
                m['beta'] = cov / var_b
            else:
                m['beta'] = 1
            
            # Benchmark return
            b_total = (1 + b_ret).prod() - 1
            m['benchmark_return'] = b_total * 100
            
            # Alpha (CAPM). Every term here must be on the SAME annual basis —
            # the risk-free rate is annual, so the portfolio and benchmark
            # returns are annualised too. Comparing a 1-month period return
            # against a full year of risk-free rate previously flipped alpha's
            # sign on short windows.
            aligned_days = len(aligned)
            if b_total > -1:
                b_cagr = (1 + b_total) ** (252 / aligned_days) - 1
            else:
                b_cagr = -1
            
            p_cagr = m['cagr'] / 100
            expected_return = rf_rate + m['beta'] * (b_cagr - rf_rate)
            m['alpha'] = (p_cagr - expected_return) * 100
            
            # Correlation and R-squared
            corr = p_ret.corr(b_ret)
            m['correlation'] = corr if not np.isnan(corr) else 0
            m['r_squared'] = m['correlation'] ** 2
            
            # Tracking Error
            tracking_diff = p_ret - b_ret
            tracking = tracking_diff.std() * np.sqrt(252)
            m['tracking_error'] = tracking * 100
            
            # Information Ratio
            if tracking > 1e-8:
                excess_ret = p_cagr - b_cagr
                m['info_ratio'] = excess_ret / tracking
            else:
                m['info_ratio'] = 0
            
            # Treynor Ratio
            if abs(m['beta']) > 0.01:
                m['treynor'] = (p_cagr - rf_rate) / m['beta']
            else:
                m['treynor'] = 0
            
            # Up/Down Capture
            up_mask = b_ret > 0
            down_mask = b_ret < 0
            
            # Capture ratios compare RETURNS, not growth factors. Dividing
            # 1.10 by 1.08 gives 101.8%; the portfolio actually captured
            # 10%/8% = 125% of the upside. Because both factors sit near 1.0,
            # the old form pinned every capture ratio near 100%.
            if up_mask.sum() > 0:
                up_p = (1 + p_ret[up_mask]).prod() - 1
                up_b = (1 + b_ret[up_mask]).prod() - 1
                if abs(up_b) > 1e-8:
                    m['up_capture'] = (up_p / up_b) * 100

            if down_mask.sum() > 0:
                down_p = (1 + p_ret[down_mask]).prod() - 1
                down_b = (1 + b_ret[down_mask]).prod() - 1
                if abs(down_b) > 1e-8:
                    m['down_capture'] = (down_p / down_b) * 100
    
    return m


def render_analysis_mode(
    df: pd.DataFrame, metrics: dict[str, float], anchor_date: datetime | None = None,
    progress_slot=None,
) -> None:
    """Render the Obsidian Quant analytics terminal."""


    # ── Header & timeframe selector ─────────────────────────────────────────
    header_desc = "Institutional-Grade Performance Analysis"
    if anchor_date:
        header_desc += f" · Anchor: {anchor_date.strftime('%b %d, %Y')}"
    render_section_header(
        "Portfolio Analytics Terminal",
        header_desc,
        icon="cpu",
        accent="cyan",
    )
    
    # Initialize session state
    if 'tf_selected' not in st.session_state:
        st.session_state.tf_selected = '1Y'
    
    # The chart window is NOT page chrome. It used to be a nine-button toolbar
    # docked under the header — a control physically distant from the thing it
    # changes. It now renders inside the comparison panel's own header (see
    # `window=True` on that panel), which is where a control that reframes a
    # chart belongs. All plots on this page share the one `tf_selected` key.
    if anchor_date:
        st.toast(f"Anchor date active · metrics from {anchor_date.strftime('%b %d, %Y')}")
        days_back = (datetime.now().date() - anchor_date).days + 1
        selected_tf = "CUSTOM"
    else:
        selected_tf = st.session_state.tf_selected
        if selected_tf == 'YTD':
            today = datetime.now()
            days_back = (today - datetime(today.year, 1, 1)).days + 1
        else:
            days_back = TIMEFRAMES[selected_tf]
    
    # =========================================================================
    # FETCH DATA (aligned to NIFTY 50 dates)
    # =========================================================================
    
    symbols = df['SYMBOL'].tolist()
    quantities = df.set_index('SYMBOL')['QUANTITY'].to_dict()

    # Themed progress card — shown only when the data window actually changes
    # (new timeframe/anchor = real fetch). Cosmetic reruns hit cache and stay
    # instant, so the bar is skipped. The native st.spinner is intentionally
    # not used (UI/UX cohesion).
    _an_key = (tuple(symbols), days_back, str(anchor_date))
    _show_prog = (st.session_state.get('_samhita_an_key') != _an_key
                  and progress_slot is not None)
    if _show_prog:
        progress_bar(progress_slot, 30, "Fetching Analysis History",
                     f"yfinance · {len(symbols)} holdings + NIFTY 50")

    portfolio_prices, benchmark_prices = fetch_analysis_data(symbols, days_back)

    if _show_prog:
        progress_bar(progress_slot, 100, "History Ready",
                     f"{selected_tf} · {len(portfolio_prices)} trading days")
        progress_slot.empty()
        st.session_state['_samhita_an_key'] = _an_key
    
    if portfolio_prices.empty:
        render_empty_state(
            "No price history available",
            "The benchmark and holdings history could not be retrieved for this "
            "window. This is usually a transient upstream outage rather than a "
            "problem with the portfolio file.",
            eyebrow="Analytics unavailable",
            action_label="Try a shorter window, or use Refresh Prices",
        )
        return
    
    # Apply anchor date filter if set
    if anchor_date:
        anchor_datetime = pd.Timestamp(anchor_date)
        portfolio_prices = portfolio_prices[portfolio_prices.index >= anchor_datetime]
        benchmark_prices = benchmark_prices[benchmark_prices.index >= anchor_datetime]
        
        if portfolio_prices.empty:
            render_empty_state(
                "Anchor date is beyond the available history",
                f"No sessions were priced on or after "
                f"<strong>{anchor_date.strftime('%b %d, %Y')}</strong>.",
                eyebrow="Anchor active",
                action_label="Pick an earlier anchor date in the rail",
            )
            return
    
    # Build the portfolio index by CHAIN-LINKING like-for-like daily returns.
    #
    # A holding that had not listed at the start of the window carries leading
    # NaNs. Summing across holdings row-wise skips those NaNs, so the day a new
    # holding's history begins its entire market value lands in the total as a
    # one-day "gain" that never happened. Measuring each day's return only
    # across holdings priced on BOTH that day and the previous one removes the
    # artefact, while still letting new holdings join the portfolio thereafter.
    holdings_value = pd.DataFrame(index=portfolio_prices.index)
    for sym in portfolio_prices.columns:
        if sym in quantities:
            holdings_value[sym] = portfolio_prices[sym] * quantities[sym]

    prev_value = holdings_value.shift(1)
    both = holdings_value.notna() & prev_value.notna()
    curr_sum = holdings_value.where(both).sum(axis=1, min_count=1)
    prev_sum = prev_value.where(both).sum(axis=1, min_count=1)

    port_returns = (curr_sum / prev_sum - 1)
    port_returns = port_returns.replace([np.inf, -np.inf], np.nan).dropna()

    # Rebuild the value curve from those returns, anchored on the market value
    # actually held on the first day of the window.
    row_sum = holdings_value.sum(axis=1, min_count=1)
    anchor = row_sum.first_valid_index()
    if anchor is None or port_returns.empty:
        render_empty_state(
            "Not enough overlapping history",
            "No two consecutive sessions have a price for the same holding, so "
            "there is no like-for-like return to chain together.",
            eyebrow="Analytics unavailable",
            action_label="Widen the window, or check the holdings' listing dates",
        )
        return
    base = float(row_sum.loc[anchor])
    port_returns = port_returns[port_returns.index > anchor]
    port_value = pd.concat([
        pd.Series([base], index=[anchor]),
        base * (1 + port_returns).cumprod(),
    ]).sort_index()
    
    # Get benchmark returns
    bench_returns = None
    if not benchmark_prices.empty and BENCHMARK_NAME in benchmark_prices.columns:
        bench_returns = benchmark_prices[BENCHMARK_NAME].pct_change(fill_method=None).dropna()
    
    # Compute metrics
    m = compute_metrics(port_returns, bench_returns)
    
    # =========================================================================
    # MAIN COMPARISON CHART
    # =========================================================================
    
    
    port_norm = (port_value / port_value.iloc[0]) * 100

    fig = go.Figure()
    port_ret_display = m.get('total_return', 0)
    fig.add_trace(go.Scatter(
        x=port_norm.index,
        y=port_norm.values,
        mode='lines',
        name=f'Portfolio ({port_ret_display:+.2f}%)',
        line=dict(color=chart_color("accent"), width=2.5),
        hovertemplate='%{x|%b %d, %Y}<br>Portfolio: %{y:.2f}<extra></extra>',
    ))

    if not benchmark_prices.empty and BENCHMARK_NAME in benchmark_prices.columns:
        bench_series = benchmark_prices[BENCHMARK_NAME].dropna()
        if len(bench_series) > 0:
            bench_norm = (bench_series / bench_series.iloc[0]) * 100
            bench_ret = ((bench_series.iloc[-1] / bench_series.iloc[0]) - 1) * 100
            fig.add_trace(go.Scatter(
                x=bench_norm.index,
                y=bench_norm.values,
                mode='lines',
                name=f'{BENCHMARK_NAME} ({bench_ret:+.2f}%)',
                line=dict(color=chart_color("cyan"), width=2, dash='dot'),
                hovertemplate=f'%{{x|%b %d, %Y}}<br>{BENCHMARK_NAME}: %{{y:.2f}}<extra></extra>',
            ))

    _apply_theme(
        fig, height=CHART_HEIGHT_LG, show_legend=True,
        margin=CHART_MARGIN_NOTITLE,
    )
    fig.update_yaxes(side='right')
    fig.update_layout(hovermode='closest')
    fig.update_xaxes(rangeslider=dict(visible=False), rangeselector=dict(visible=False))

    render_chart_panel(fig, key="portfolio-vs-benchmark",
                       units="indexed to 100", window=True)

    # ── Returns & Risk-Adjusted Performance ─────────────────────────────────
    render_section_header(
        "Returns & Risk-Adjusted Performance",
        "What the window returned, and what it cost in risk to earn it",
        icon="zap", accent="emerald",
    )
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        val = m.get('total_return', 0)
        _cagr_note = (f"CAGR: {m.get('cagr', 0):+.1f}%" if m.get('annualised', True)
                      else f"Annualised: {m.get('cagr', 0):+.1f}% · short window")
        render_metric_card("Period Return", f"{val:+.2f}%",
                           subtext=_cagr_note,
                           color_class='success' if val >= 0 else 'danger')
    with c2:
        alpha = m.get('alpha', 0)
        cls = 'success' if alpha > 0 else 'danger' if alpha < 0 else 'neutral'
        render_metric_card("Alpha", f"{alpha:+.2f}%", subtext="Excess return",
                           color_class=cls)
    with c3:
        sharpe = m.get('sharpe', 0)
        cls = 'success' if sharpe > 1 else 'warning' if sharpe > 0.5 else 'danger'
        render_metric_card("Sharpe", f"{sharpe:.2f}", subtext="Rf = 6.5%",
                           color_class=cls)
    with c4:
        sortino = m.get('sortino', 0)
        cls = 'success' if sortino > 1.5 else 'warning' if sortino > 0.5 else 'danger'
        render_metric_card("Sortino", f"{sortino:.2f}", subtext="Downside risk",
                           color_class=cls)
    with c5:
        calmar = m.get('calmar', 0)
        cls = 'success' if calmar > 1 else 'warning' if calmar > 0.5 else 'danger'
        render_metric_card("Calmar", f"{calmar:.2f}", subtext="Return / MaxDD",
                           color_class=cls)
    with c6:
        ir = m.get('info_ratio', 0)
        cls = 'success' if ir > 0.5 else 'warning' if ir > 0 else 'danger'
        render_metric_card("Info Ratio", f"{ir:.2f}", subtext="Active return / TE",
                           color_class=cls)

    # ── Risk Metrics ────────────────────────────────────────────────────────
    render_section_header(
        "Risk Metrics",
        "Dispersion, drawdown and tail loss over the selected window",
        icon="shield", accent="rose",
    )
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        vol = m.get('volatility', 0)
        render_metric_card("Volatility", f"{vol:.1f}%", subtext="Annualized",
                           color_class="warning")
    with c2:
        mdd = m.get('max_drawdown', 0)
        cls = 'danger' if mdd < -20 else 'warning' if mdd < -10 else 'success'
        render_metric_card("Max Drawdown", f"{mdd:.1f}%", subtext="Peak to trough",
                           color_class=cls)
    with c3:
        var95 = m.get('var_95', 0)
        render_metric_card("VaR (95%)", f"{var95:.2f}%", subtext="Daily at risk",
                           color_class="danger")
    with c4:
        cvar = m.get('cvar_95', 0)
        render_metric_card("CVaR (95%)", f"{cvar:.2f}%", subtext="Expected shortfall",
                           color_class="danger")
    with c5:
        beta = m.get('beta', 1)
        cls = 'warning' if beta > 1.2 else 'info' if beta < 0.8 else 'neutral'
        render_metric_card("Beta", f"{beta:.2f}", subtext="Market sensitivity",
                           color_class=cls)
    with c6:
        te = m.get('tracking_error', 0)
        render_metric_card("Tracking Error", f"{te:.1f}%", subtext="vs Benchmark",
                           color_class="info")

    # ── Benchmark Comparison ────────────────────────────────────────────────
    render_section_header(
        "Benchmark Comparison",
        "The portfolio against NIFTY 50 · beta, capture and tracking error",
        icon="compass", accent="cyan",
    )
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        bench_ret = m.get('benchmark_return', 0)
        render_metric_card("Benchmark", f"{bench_ret:+.1f}%", subtext=BENCHMARK_NAME,
                           color_class='success' if bench_ret >= 0 else 'danger')
    with c2:
        excess = m.get('total_return', 0) - m.get('benchmark_return', 0)
        render_metric_card("Excess Return", f"{excess:+.1f}%", subtext="vs Benchmark",
                           color_class='success' if excess > 0 else 'danger')
    with c3:
        up_cap = m.get('up_capture', 100)
        render_metric_card("Up Capture", f"{up_cap:.0f}%", subtext="Bull market",
                           color_class='success' if up_cap > 100 else 'warning')
    with c4:
        down_cap = m.get('down_capture', 100)
        render_metric_card("Down Capture", f"{down_cap:.0f}%", subtext="Bear market",
                           color_class='success' if down_cap < 100 else 'warning')
    with c5:
        r2 = m.get('r_squared', 0)
        render_metric_card("R-Squared", f"{r2:.2f}", subtext="Explained variance",
                           color_class="info")
    with c6:
        corr = m.get('correlation', 0)
        render_metric_card("Correlation", f"{corr:.2f}", subtext="vs Benchmark",
                           color_class="info")
    
    # =========================================================================
    # DRAWDOWN & DISTRIBUTION CHARTS
    # =========================================================================
    
    
    col_dd, col_dist = st.columns(2)

    with col_dd:
        render_section_header(
            "Drawdown Analysis",
            "Decline from each running peak, and how long it lasted",
            icon="activity", accent="rose",
        )
        dd_series = m.get('drawdown_series', pd.Series())
        if len(dd_series) > 0:
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=dd_series.index,
                y=dd_series.values,
                mode='lines',
                fill='tozeroy',
                line=dict(color=chart_color("rose"), width=1),
                fillcolor=chart_rgba("rose", 0.25),
                hovertemplate='%{x|%b %d, %Y}<br>Drawdown: %{y:.2f}%<extra></extra>',
            ))
            fig_dd.add_hline(
                y=m.get('max_drawdown', 0),
                line_dash="dash",
                line_color=chart_color("accent"),
                annotation_text=f"Max: {m.get('max_drawdown', 0):.1f}%",
                annotation_position="right",
            )
            _apply_theme(
                fig_dd, height=CHART_HEIGHT_MD, show_legend=False,
                margin=CHART_MARGIN,
                title="Underwater Equity Curve",
            )
            render_chart_panel(fig_dd, key="drawdown", units="% from peak")

    with col_dist:
        render_section_header(
            "Returns Distribution",
            "The shape of daily returns · frequency, skew and tails",
            icon="bar-chart", accent="emerald",
        )
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=port_returns * 100,
            nbinsx=40,
            marker_color=chart_color("accent"),
            opacity=0.78,
            hovertemplate='Return: %{x:.2f}%<br>Count: %{y}<extra></extra>',
        ))
        fig_hist.add_vline(x=0, line_dash="dash", line_color=ink_subtle(), line_width=1)
        fig_hist.add_vline(
            x=port_returns.mean() * 100,
            line_dash="dot",
            line_color=chart_color("emerald"),
            annotation_text=f"μ: {port_returns.mean()*100:.2f}%",
            annotation_position="top",
            # The label carries its line's own claim, so the reader does not
            # have to trace a dotted rule back to a legend that is not there.
            annotation_font=dict(size=10, family=CHART_FONT,
                                 color=chart_color("emerald")),
        )
        fig_hist.add_vline(
            x=m.get('var_95', 0),
            line_dash="dash",
            line_color=chart_color("rose"),
            annotation_text=f"VaR: {m.get('var_95', 0):.1f}%",
            # TOP, like the mean beside it. "bottom left" put this label at the
            # foot of the plot — which on a histogram is exactly where the bars
            # are, so it read as grey type over five blue columns. A reference
            # line's label belongs clear of the marks it is a reference FOR.
            annotation_position="top",
            annotation_font=dict(size=10, family=CHART_FONT,
                                 color=chart_color("rose")),
        )
        _apply_theme(
            fig_hist, height=CHART_HEIGHT_MD, show_legend=False,
            margin=CHART_MARGIN,
            title="Daily Returns Histogram",
            x_title='Daily Return (%)',
        )
        render_chart_panel(fig_hist, key="return-dist", units="daily %")
    
    # ── Rolling Analytics (dynamic window based on timeframe) ───────────────
    data_length = len(port_returns)

    if data_length < 15:
        pass
    else:
        rolling_window = min(63, max(10, data_length // 3))

        render_section_header(
            "Rolling Analytics",
            f"Metrics recomputed over a moving {rolling_window}-day window",
            icon="activity",
            accent="violet",
        )

        col_rs, col_rb = st.columns(2)

        with col_rs:
            # Excess over the risk-free rate, matching the headline Sharpe —
            # otherwise this chart and the Sharpe card disagree, and the
            # "Target = 1" line below is read against the wrong number.
            roll_mean = (port_returns - RF_RATE / 252).rolling(rolling_window).mean()
            roll_std = port_returns.rolling(rolling_window).std()
            roll_sharpe = (roll_mean / roll_std) * np.sqrt(252)
            roll_sharpe = roll_sharpe.dropna()

            if len(roll_sharpe) > 0:
                fig_rs = go.Figure()
                fig_rs.add_trace(go.Scatter(
                    x=roll_sharpe.index,
                    y=roll_sharpe.values,
                    mode='lines',
                    line=dict(color=chart_color("accent"), width=1.5),
                    hovertemplate='%{x|%b %d, %Y}<br>Sharpe: %{y:.2f}<extra></extra>',
                ))
                fig_rs.add_hline(y=1, line_dash="dash", line_color=chart_color("emerald"),
                                 annotation_text="Target", annotation_position="right")
                fig_rs.add_hline(y=0, line_dash="dash", line_color=ink_subtle())
                _apply_theme(
                    fig_rs, height=CHART_HEIGHT_SM, show_legend=False,
                    margin=CHART_MARGIN,
                    title="Rolling Sharpe Ratio",
                )
                fig_rs.update_xaxes(tickformat='%b %Y')
                render_chart_panel(fig_rs, key="rolling-sharpe",
                                   units=f"{rolling_window}d rolling")

        with col_rb:
            if bench_returns is not None and len(bench_returns) > rolling_window:
                aligned = pd.concat([port_returns, bench_returns], axis=1).dropna()
                aligned.columns = ['Port', 'Bench']

                if len(aligned) > rolling_window:
                    roll_betas = []
                    roll_dates = []
                    for i in range(rolling_window, len(aligned)):
                        w = aligned.iloc[i-rolling_window:i]
                        cov = np.cov(w['Port'], w['Bench'])[0, 1]
                        var = w['Bench'].var()
                        roll_betas.append(cov / var if var > 0 else 1)
                        roll_dates.append(aligned.index[i])

                    if len(roll_betas) > 0:
                        fig_rb = go.Figure()
                        fig_rb.add_trace(go.Scatter(
                            x=roll_dates,
                            y=roll_betas,
                            mode='lines',
                            line=dict(color=chart_color("cyan"), width=1.5),
                            hovertemplate='%{x|%b %d, %Y}<br>Beta: %{y:.2f}<extra></extra>',
                        ))
                        fig_rb.add_hline(y=1, line_dash="dash", line_color=ink_subtle(),
                                         annotation_text="Market", annotation_position="right")
                        _apply_theme(
                            fig_rb, height=CHART_HEIGHT_SM, show_legend=False,
                            margin=CHART_MARGIN,
                            title=f"Rolling Beta vs {BENCHMARK_NAME}",
                        )
                        fig_rb.update_xaxes(tickformat='%b %Y')
                        render_chart_panel(fig_rb, key="rolling-beta",
                                           units=f"{rolling_window}d rolling")

    # ── Monthly Returns Heatmap ─────────────────────────────────────────────
    render_section_header(
        "Monthly Returns Heatmap",
        "Month-over-month return by calendar year · a starred year is partial",
        icon="grid", accent="emerald",
    )
    
    # Calculate monthly returns
    monthly = port_value.resample('ME').last().pct_change(fill_method=None).dropna() * 100
    
    if len(monthly) > 1:
        # Create a proper month-year structure
        monthly_df = pd.DataFrame({
            'Year': monthly.index.year,
            'Month': monthly.index.month,
            'Return': monthly.values
        })
        
        # Get unique years
        years = sorted(monthly_df['Year'].unique())
        
        # Create pivot with all 12 months as columns
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        
        # Build heatmap data manually to ensure proper structure
        heatmap_data = []
        year_labels = []
        
        for year in years:
            year_data = monthly_df[monthly_df['Year'] == year]
            row = []
            for month in range(1, 13):
                month_return = year_data[year_data['Month'] == month]['Return'].values
                if len(month_return) > 0:
                    row.append(month_return[0])
                else:
                    row.append(np.nan)
            
            # Year column. This is the return over the part of the year the
            # window actually covers — for the earliest year that is rarely
            # 1 January, so partial years are marked rather than presented as
            # a full-year figure.
            year_slice = port_value[port_value.index.year == year]
            if len(year_slice) > 0 and year_slice.iloc[0] > 0:
                year_ret = ((year_slice.iloc[-1] / year_slice.iloc[0]) - 1) * 100
                partial = year_slice.index[0].month != 1
            else:
                year_ret = np.nan
                partial = False
            row.append(year_ret)

            heatmap_data.append(row)
            year_labels.append(f"{year}*" if partial else str(year))
        
        # Column labels
        col_labels = month_names + ['YEAR']
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=col_labels,
            y=year_labels,
            colorscale=[[0, chart_color("rose")], [0.5, panel_bg()], [1, chart_color("emerald")]],
            zmid=0,
            text=[[f"{v:.1f}%" if pd.notna(v) else "" for v in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont=dict(size=10, color=ink(), family="JetBrains Mono, monospace"),
            hovertemplate="Year: %{y}<br>%{x}: %{z:.2f}%<extra></extra>",
            showscale=False,
        ))

        # A heatmap has axes but they are CATEGORY axes labelling a tiling —
        # a grid, a zero line and a crosshair over it are furniture for a plot
        # that isn't there. It takes the shared canvas/font/hover and then its
        # own two axes, at the app's own tick size.
        _apply_theme(fig_heat, height=max(CHART_HEIGHT_SM, len(years) * 38 + 80),
                     margin=CHART_MARGIN_HEATMAP, axes=False)
        _tick = dict(size=9, family="JetBrains Mono, monospace", color=ink_subtle())
        fig_heat.update_xaxes(side='top', tickangle=0, type='category', dtick=1,
                              showgrid=False, zeroline=False, tickfont=_tick)
        fig_heat.update_yaxes(autorange='reversed', type='category', dtick=1,
                              showgrid=False, zeroline=False, tickfont=_tick)

        render_chart_panel(fig_heat, key="monthly-heatmap", units="monthly %")

    # ── Holding Attribution ─────────────────────────────────────────────────
    render_section_header(
        "Holding Attribution",
        "Each holding's contribution to the window's return · Carino-linked, so they sum to it",
        icon="link", accent="cyan",
    )

    # Attribution is built from each holding's DAILY weight, not its weight
    # today: applying today's weight to a year-old return credits the wrong
    # holdings, and mixing holdings that only listed part-way through the
    # window compares different periods. Daily contributions are then
    # Carino-linked, which is what makes them sum exactly to the compounded
    # portfolio return instead of drifting away from it.
    hv_prev = holdings_value.shift(1)
    daily_pairs = holdings_value.notna() & hv_prev.notna()
    base_prev = hv_prev.where(daily_pairs).sum(axis=1, min_count=1)
    weights = hv_prev.where(daily_pairs).div(base_prev, axis=0)
    hold_returns = (holdings_value.where(daily_pairs) / hv_prev.where(daily_pairs)) - 1
    daily_contrib = (weights * hold_returns).reindex(port_returns.index)

    # Carino scaling: k_t on each day, K over the whole window.
    total_r = float((1 + port_returns).prod() - 1)
    if abs(total_r) > 1e-12 and total_r > -1:
        K = np.log1p(total_r) / total_r
        safe = np.where(port_returns.values > -1 + 1e-12, port_returns.values, np.nan)
        k_t = np.where(np.abs(safe) > 1e-12,
                       np.log1p(safe) / np.where(safe == 0, 1, safe),
                       1.0)
        scale = pd.Series(k_t / K, index=port_returns.index)
        scale = scale.replace([np.inf, -np.inf], np.nan).fillna(1.0)
    else:
        scale = pd.Series(1.0, index=port_returns.index)

    linked = daily_contrib.mul(scale, axis=0).sum(axis=0, min_count=1)
    avg_weight = weights.reindex(port_returns.index).mean(axis=0) * 100

    attribution = []
    for sym in symbols:
        if sym in portfolio_prices.columns and sym in linked.index:
            prices = portfolio_prices[sym].dropna()
            if len(prices) > 1 and pd.notna(linked[sym]):
                attribution.append({
                    'Symbol': sym,
                    'Return': (prices.iloc[-1] / prices.iloc[0] - 1) * 100,
                    'Weight': float(avg_weight.get(sym, 0.0)),
                    'Contribution': float(linked[sym]) * 100,
                })

    if attribution:
        attr_df = pd.DataFrame(attribution).sort_values('Contribution', ascending=True)
        fig_attr = go.Figure()
        colors = [chart_color("emerald") if x >= 0 else chart_color("rose") for x in attr_df['Contribution']]
        fig_attr.add_trace(go.Bar(
            y=attr_df['Symbol'],
            x=attr_df['Contribution'],
            orientation='h',
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in attr_df['Contribution']],
            # OUTSIDE: `auto` drops the value inside the bar and paints it
            # in the app's ink — the same darkness as the saturated fill
            # it lands on, and rotated 90 degrees in a narrow column.
            textposition='outside',
            cliponaxis=False,
            textfont=dict(size=10, color=ink_muted(), family=CHART_FONT),
            hovertemplate="<b>%{y}</b><br>Return: %{customdata[0]:.1f}%<br>Weight: %{customdata[1]:.1f}%<br>Contribution: %{x:.2f}%<extra></extra>",
            customdata=attr_df[['Return', 'Weight']].values,
        ))
        _apply_theme(
            fig_attr, height=max(CHART_HEIGHT_MD, len(attr_df) * 25 + 70),
            show_legend=False, margin=CHART_MARGIN_BAR,
        )
        fig_attr.update_yaxes(showgrid=False, zeroline=False)
        _pad_for_value_labels(fig_attr)
        render_chart_panel(fig_attr, key="attribution",
                           units="pp of period return")
    
    # =========================================================================
    # STATISTICS TABLE
    # =========================================================================
    
    
    with st.expander("Detailed Statistics", expanded=False):
        col_s1, col_s2, col_s3 = st.columns(3)

        with col_s1:
            render_sub_header("Performance")
            _tr, _cg = m.get('total_return', 0), m.get('cagr', 0)
            render_rail_readout([
                ("Total Return", f"{_tr:+.2f}%", "long" if _tr >= 0 else "short"),
                ("CAGR" if m.get('annualised', True) else "Annualised",
                 f"{_cg:+.2f}%", "long" if _cg >= 0 else "short"),
                ("Best Day", f"{m.get('best_day', 0):+.2f}%", "long"),
                ("Worst Day", f"{m.get('worst_day', 0):.2f}%", "short"),
                ("Win Rate", f"{m.get('win_rate', 0):.1f}%", ""),
                ("Win / Lose", f"{m.get('win_days', 0)} / {m.get('lose_days', 0)}", ""),
                ("Profit Factor", f"{m.get('profit_factor', 0):.2f}", ""),
            ])

        with col_s2:
            render_sub_header("Risk")
            render_rail_readout([
                ("Volatility (Ann.)", f"{m.get('volatility', 0):.2f}%", ""),
                ("Daily Volatility", f"{m.get('daily_vol', 0):.3f}%", ""),
                ("Max Drawdown", f"{m.get('max_drawdown', 0):.2f}%", "short"),
                ("VaR 95%", f"{m.get('var_95', 0):.2f}%", "caution"),
                ("VaR 99%", f"{m.get('var_99', 0):.2f}%", "caution"),
                ("CVaR 95%", f"{m.get('cvar_95', 0):.2f}%", "short"),
            ])

        with col_s3:
            render_sub_header("Distribution")
            render_rail_readout([
                ("Skewness", f"{m.get('skewness', 0):.3f}", ""),
                ("Kurtosis", f"{m.get('kurtosis', 0):.3f}", ""),
                ("Sharpe", f"{m.get('sharpe', 0):.2f}", ""),
                ("Sortino", f"{m.get('sortino', 0):.2f}", ""),
                ("Calmar", f"{m.get('calmar', 0):.2f}", ""),
                ("Treynor", f"{m.get('treynor', 0):.3f}", ""),
            ])

    st.toast(f"Analytics loaded for {selected_tf}")


if __name__ == "__main__":
    main()
