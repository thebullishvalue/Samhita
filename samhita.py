
# -*- coding: utf-8 -*-
"""
SAMHITA (संहिता) - Portfolio Tracker | A @thebullishvalue Product
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Real-time portfolio analytics with performance tracking.
Time series analysis and historical performance insights.

UI — "Obsidian Quant" Institutional Research Terminal design language.
"""

from __future__ import annotations

import sys
import time
import uuid
from datetime import datetime, timedelta, timezone
from io import BytesIO
from typing import Any

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import yfinance as yf
from plotly.subplots import make_subplots

from ui.theme import (
    CHART_HEIGHT_LG,
    CHART_HEIGHT_MD,
    CHART_HEIGHT_SM,
    CHART_MARGIN,
    CHART_MARGIN_BAR,
    CHART_MARGIN_HEATMAP,
    CHART_MARGIN_NOAXIS,
    CHART_MARGIN_NOTITLE,
    CHART_MARGIN_ROTATED,
    PLOTLY_FONT,
    PLOTLY_HOVERLABEL,
    chart_layout,
    inject_css,
    progress_bar,
    style_axes,
)
from ui.components import (
    render_header,
    render_metric_card,
    render_section_header,
)

# --- Constants ---
VERSION = "v1.2.0"
PRODUCT_NAME = ""
COMPANY = "@thebullishvalue"

# Obsidian Quant chart palette
CHART_AMBER = "#D4A853"
CHART_AMBER_GLOW = "rgba(212, 168, 83, 0.15)"
CHART_EMERALD = "#2DD4A8"
CHART_ROSE = "#E8555A"
CHART_CYAN = "#06B6D4"
CHART_VIOLET = "#8B5CF6"
CHART_INK = "#F1F5F9"
CHART_INK_MUTED = "#94A3B8"
CHART_INK_SUBTLE = "#64748B"
CHART_GRID = "rgba(255,255,255,0.035)"

# Streamlit page configuration
st.set_page_config(
    page_title="SAMHITA | Portfolio Tracker",
    layout="wide",
    initial_sidebar_state="collapsed",
)

inject_css()


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
# Secondary data infrastructure (fallback when yfinance is non-responsive).
#
# yfinance stays the PRIMARY source and the portfolio SYMBOL convention is
# unchanged (no dot -> NSE; ".BO" -> BSE; ".NS" -> NSE). These helpers adapt
# that convention to each secondary source's naming, then fill ONLY the
# symbols yfinance left as NaN.
#
# Per exchange: live first, EOD bhavcopy as a post-close backstop.
#   NSE  live -> NseKit.cm_live_equity_full_info ; EOD -> jugaad bhavcopy
#   BSE  live -> bse.quote (scrip code by name)   ; EOD -> bse bhavcopy
# Every source is optional and lazily imported: a missing/failing source is
# silently skipped, so the app always degrades gracefully back to yfinance.
# ---------------------------------------------------------------------------

def _classify(symbol: str) -> tuple[str, str] | None:
    """Map a raw portfolio symbol to (exchange, bare_symbol) for the fallbacks.

    Mirrors _to_yf_ticker: no dot or ".NS" -> NSE; ".BO" -> BSE.
    Returns None for symbols/exchanges we have no fallback for.
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


def _fallback_nse_live(bare_symbols: list[str]) -> dict[str, tuple[float, float]]:
    """NseKit live quotes, per symbol. {bare: (last, prev_close)}."""
    out: dict[str, tuple[float, float]] = {}
    try:
        from NseKit import Nse
        nse = Nse()
    except Exception as e:
        log.warning(f"NseKit unavailable ({type(e).__name__}); skipping NSE live")
        return out
    for bare in bare_symbols:
        try:
            d = nse.cm_live_equity_full_info(bare)
            if d:
                out[bare] = (_num(d.get('LastTradedPrice')), _num(d.get('PreviousClose')))
                log.detail(f"NseKit · {bare} → {out[bare][0]}")
        except Exception:
            continue
    return out


def _fallback_bse_live(bare_symbols: list[str]) -> dict[str, tuple[float, float]]:
    """bse.quote live quotes, per symbol (scrip code resolved by name)."""
    out: dict[str, tuple[float, float]] = {}
    try:
        import tempfile
        from bse import BSE
        b = BSE(download_folder=tempfile.gettempdir())
    except Exception as e:
        log.warning(f"bse unavailable ({type(e).__name__}); skipping BSE live")
        return out
    try:
        for bare in bare_symbols:
            try:
                code = b.getScripCode(bare)
                if not code:
                    continue
                q = b.quote(code)
                if q:
                    out[bare] = (_num(q.get('LTP')), _num(q.get('PrevClose')))
                    log.detail(f"bse · {bare} (#{code}) → {out[bare][0]}")
            except Exception:
                continue
    finally:
        try:
            b.exit()
        except Exception:
            pass
    return out


def _bhav_lookup(df: pd.DataFrame, eq_only: bool) -> dict[str, tuple[float, float]]:
    """Build {TckrSymb: (close, prev_close)} from a UDiFF bhavcopy DataFrame."""
    lookup: dict[str, tuple[float, float]] = {}
    if df is None or 'TckrSymb' not in df.columns:
        return lookup
    rows = df
    if eq_only and 'SctySrs' in df.columns:
        rows = df[df['SctySrs'].astype(str).str.strip() == 'EQ']
    for _, r in rows.iterrows():
        sym = str(r['TckrSymb']).strip()
        if sym and sym not in lookup:
            lookup[sym] = (_num(r.get('ClsPric')), _num(r.get('PrvsClsgPric')))
    return lookup


def _fallback_nse_bhav(bare_symbols: list[str]) -> dict[str, tuple[float, float]]:
    """Most-recent NSE EOD bhavcopy (jugaad), matched on TckrSymb."""
    try:
        import tempfile
        from jugaad_data.nse import bhavcopy_save
    except Exception:
        return {}
    folder, today = tempfile.gettempdir(), datetime.now().date()
    for back in range(0, 7):
        try:
            d = today - timedelta(days=back)
            path = bhavcopy_save(d, folder)
            df = pd.read_csv(path)
            df.columns = [c.strip() for c in df.columns]
            lookup = _bhav_lookup(df, eq_only=True)
            log.detail(f"NSE bhavcopy {d:%d-%b-%Y} loaded ({len(lookup)} scrips)")
            return {b: lookup[b] for b in bare_symbols if b in lookup}
        except Exception:
            continue
    log.warning("NSE bhavcopy unavailable (last 7 days)")
    return {}


def _fallback_bse_bhav(bare_symbols: list[str]) -> dict[str, tuple[float, float]]:
    """Most-recent BSE EOD bhavcopy (bse), matched on TckrSymb."""
    try:
        import tempfile
        from bse import BSE
        b = BSE(download_folder=tempfile.gettempdir())
    except Exception:
        return {}
    try:
        today = datetime.now().date()
        for back in range(0, 7):
            try:
                d = today - timedelta(days=back)
                path = b.bhavcopyReport(d)
                df = pd.read_csv(path)
                df.columns = [c.strip() for c in df.columns]
                lookup = _bhav_lookup(df, eq_only=False)
                log.detail(f"BSE bhavcopy {d:%d-%b-%Y} loaded ({len(lookup)} scrips)")
                return {s: lookup[s] for s in bare_symbols if s in lookup}
            except Exception:
                continue
        log.warning("BSE bhavcopy unavailable (last 7 days)")
    finally:
        try:
            b.exit()
        except Exception:
            pass
    return {}


def _merge_live_bhav(
    bare_to_orig: dict[str, str],
    live: dict[str, tuple[float, float]],
    bhav: dict[str, tuple[float, float]],
    resolved: dict[str, tuple[float, float]],
) -> None:
    """Prefer live (must carry a last price); fall back to bhavcopy."""
    for bare, orig in bare_to_orig.items():
        lq, bq = live.get(bare), bhav.get(bare)
        if lq and not pd.isna(lq[0]):
            resolved[orig] = lq
        elif bq and not pd.isna(bq[0]):
            resolved[orig] = bq
        elif lq:
            resolved[orig] = lq


@st.cache_data(ttl=300, show_spinner=False)
def _fetch_fallback_quotes(symbols: tuple[str, ...]) -> dict[str, tuple[float, float]]:
    """Resolve {original_symbol: (last, prev_close)} from secondary sources.

    Live-first per exchange, EOD bhavcopy as a backstop. Only called for the
    symbols yfinance could not price.
    """
    if not symbols:
        return {}
    nse: dict[str, str] = {}
    bse: dict[str, str] = {}
    other: list[str] = []
    for s in symbols:
        c = _classify(s)
        if not c:
            other.append(s)
            continue
        exch, bare = c
        (nse if exch == 'NSE' else bse)[bare] = s

    t0 = time.perf_counter()
    log.step(f"SECONDARY · {len(symbols)} unpriced → NSE:{len(nse)} BSE:{len(bse)}"
             + (f" · {len(other)} unsupported" if other else ""))

    resolved: dict[str, tuple[float, float]] = {}

    if nse:
        log.detail(f"NSE live (NseKit) · {len(nse)} symbol(s)")
        live = _fallback_nse_live(list(nse))
        still = [b for b in nse if b not in live or pd.isna(live[b][0])]
        if still:
            log.detail(f"NSE backstop (bhavcopy) · {len(still)} unresolved live")
        bhav = _fallback_nse_bhav(still) if still else {}
        _merge_live_bhav(nse, live, bhav, resolved)

    if bse:
        log.detail(f"BSE live (bse.quote) · {len(bse)} symbol(s)")
        live = _fallback_bse_live(list(bse))
        still = [b for b in bse if b not in live or pd.isna(live[b][0])]
        if still:
            log.detail(f"BSE backstop (bhavcopy) · {len(still)} unresolved live")
        bhav = _fallback_bse_bhav(still) if still else {}
        _merge_live_bhav(bse, live, bhav, resolved)

    dt = time.perf_counter() - t0
    got = sum(1 for v in resolved.values() if not pd.isna(v[0]))
    log.success(f"Secondary resolved {got}/{len(symbols)} in {dt:.1f}s")
    return resolved


# Function to fetch current prices from yfinance
@st.cache_data(ttl=300, show_spinner=False)  # 5 min cache
def fetch_current_prices(symbols: list[str]) -> dict[str, float | Any]:
    """
    Fetches the latest closing price for a list of symbols with the .NS suffix.
    Returns a dictionary of {original_symbol: price}.

    Uses the same proven approach as returns.py:
    - Daily data (no intraday interval) to avoid rate limits
    - Single bulk download for all tickers
    - 5-day period to handle weekends/holidays

    Diagnostics are routed to the terminal log (see _Console); no Streamlit
    banners/spinners are emitted here so the UI stays cohesive.
    """
    if not symbols:
        return {}

    # Body runs only on a cache miss → mark that a real fetch occurred so the
    # caller logs the resolution summary once (not on cache-hit reruns).
    _FETCH_RAN["primary"] = True

    # Build ticker list (.NS fallback) and a ticker -> original symbol map
    ticker_map = {
        _to_yf_ticker(s): s for s in symbols if s and isinstance(s, str)
    }
    tickers_with_suffix = list(ticker_map.keys())

    log.section("SAMHITA · CURRENT PRICES")
    log.step(f"PRIMARY · yfinance · {len(tickers_with_suffix)} symbol(s) (period=5d)")
    t0 = time.perf_counter()

    prices = {s: np.nan for s in symbols}

    try:
        # Fetch daily data for last 5 days (handles weekends/holidays)
        # NO interval parameter = daily data = less rate limiting
        data = yf.download(
            tickers=tickers_with_suffix,
            period="5d",
            progress=False,
            auto_adjust=False
        )

        if data.empty:
            log.error("yfinance returned empty data")
        else:
            close_prices = data['Close'] if 'Close' in data.columns.get_level_values(0) else None
            if close_prices is None:
                log.error("yfinance response had no 'Close' column")
            elif close_prices.empty:
                log.error("yfinance 'Close' frame was empty")
            elif len(tickers_with_suffix) == 1:
                # Single ticker case: close_prices is a Series
                ticker = tickers_with_suffix[0]
                original = ticker_map[ticker]
                series = close_prices.dropna()
                if not series.empty:
                    prices[original] = float(series.iloc[-1])
            else:
                # Multiple tickers case: close_prices is a DataFrame
                latest_prices = close_prices.iloc[-1]
                for ticker in tickers_with_suffix:
                    original = ticker_map[ticker]
                    try:
                        price = latest_prices[ticker]
                        prices[original] = float(price) if not pd.isna(price) else np.nan
                    except (KeyError, TypeError):
                        prices[original] = np.nan

    except Exception as e:
        log.error(f"yfinance request failed: {type(e).__name__}: {e}")

    dt = time.perf_counter() - t0
    failed = [s for s in symbols if pd.isna(prices.get(s))]
    priced = len(symbols) - len(failed)
    if failed:
        log.warning(f"Primary priced {priced}/{len(symbols)} in {dt:.1f}s")
        log.item("Unpriced", _fmt_symlist(failed))
        log.detail("Handing off to secondary sources…")
    else:
        log.success(f"Primary priced {priced}/{len(symbols)} in {dt:.1f}s")

    return prices
    

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
        st.error(f"File '{file_path}' not found. Please upload the data file.")
        return None

# Function to fetch previous day close prices for Today Return calculation
@st.cache_data(ttl=300, show_spinner=False)
def fetch_previous_close(symbols: list[str]) -> dict[str, float | Any]:
    """Fetch previous trading day close prices for calculating today return."""
    if not symbols:
        return {}
    
    prices = {}
    ticker_map = {_to_yf_ticker(s): s for s in symbols}
    tickers_with_suffix = list(ticker_map.keys())

    try:
        # Fetch 5 days of data to ensure we get previous close
        data = yf.download(
            tickers=tickers_with_suffix,
            period='5d',
            interval='1d',
            progress=False,
            threads=True,
            auto_adjust=False
        )

        if data.empty:
            return {s: np.nan for s in symbols}
        
        close_prices = data['Close']
        
        # Single ticker case
        if len(tickers_with_suffix) == 1:
            ticker = tickers_with_suffix[0]
            original = ticker_map[ticker]
            if len(close_prices.dropna()) >= 2:
                prev_close = close_prices.dropna().iloc[-2]  # Second to last
                prices[original] = float(prev_close)
            else:
                prices[original] = np.nan
        else:
            # Multiple tickers - get second to last row
            if len(close_prices) >= 2:
                prev_prices = close_prices.iloc[-2]
                for ticker in tickers_with_suffix:
                    original = ticker_map[ticker]
                    try:
                        price = prev_prices[ticker]
                        prices[original] = float(price) if not pd.isna(price) else np.nan
                    except (KeyError, TypeError):
                        prices[original] = np.nan
            else:
                return {s: np.nan for s in symbols}
                
    except Exception as e:
        return {s: np.nan for s in symbols}
    
    return prices

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
    _p(20, "Fetching live prices", f"yfinance · {len(symbols)} holdings")
    price_map = fetch_current_prices(symbols)

    # 2. Fetch previous close for today's return
    _p(45, "Reconciling previous close", "Today's change basis")
    prev_close_map = fetch_previous_close(symbols)

    # 2b. Secondary sources (live-first, EOD bhavcopy backstop) fill ONLY the
    # symbols yfinance could not price. yfinance remains the primary source.
    missing = [s for s in symbols if pd.isna(price_map.get(s, np.nan))]
    primary_count = len(symbols) - len(missing)
    secondary_count = 0
    if missing:
        _p(65, "Querying secondary sources",
           f"{len(missing)} unpriced · NseKit / BSE / bhavcopy")
        fb = _fetch_fallback_quotes(tuple(sorted(missing)))
        for s, (last, prev) in fb.items():
            if not pd.isna(last):
                price_map[s] = last
                secondary_count += 1
            if pd.isna(prev_close_map.get(s, np.nan)) and not pd.isna(prev):
                prev_close_map[s] = prev

    _p(90, "Computing analytics", f"{len(symbols)} holdings")

    # 3. Update CURRENT PRICE column using fetched data
    df['FETCHED PRICE'] = df['SYMBOL'].map(price_map)
    df['CURRENT PRICE'] = df['FETCHED PRICE'].fillna(df.get('CURRENT PRICE', df['AVERAGE PRICE']))
    
    # 4. Add previous close for today's return calculation
    df['PREV CLOSE'] = df['SYMBOL'].map(prev_close_map)

    # Final resolution summary -> terminal log only (no Streamlit banner).
    # Logged once per real fetch; skipped on cache-hit reruns so the box is
    # never duplicated.
    if _FETCH_RAN["primary"]:
        unresolved = df.loc[df['FETCHED PRICE'].isnull(), 'SYMBOL'].tolist()
        log.summary("PRICE RESOLUTION", {
            "Holdings": len(symbols),
            "Primary (yfinance)": primary_count,
            "Secondary (fallback)": secondary_count,
            "Avg-price fallback": f"{len(unresolved)}" + (
                f" ({_fmt_symlist(unresolved)})" if unresolved else ""
            ),
        })
        log.line("═", 70)

    # 5. Perform calculations using the updated 'CURRENT PRICE'
    df['INVESTED'] = df['QUANTITY'] * df['AVERAGE PRICE']
    df['CURR. VALUE'] = df['QUANTITY'] * df['CURRENT PRICE']
    df['GAIN'] = df['CURR. VALUE'] - df['INVESTED']
    
    # Calculate today's change per holding
    df['TODAY CHANGE'] = np.where(
        df['PREV CLOSE'].notna(),
        (df['CURRENT PRICE'] - df['PREV CLOSE']) * df['QUANTITY'],
        0
    )
    df['TODAY %'] = np.where(
        (df['PREV CLOSE'].notna()) & (df['PREV CLOSE'] != 0),
        (df['CURRENT PRICE'] - df['PREV CLOSE']) / df['PREV CLOSE'] * 100,
        0
    )
    
    # Avoid division by zero
    df['GAIN %'] = np.where(df['INVESTED'] != 0, df['GAIN'] / df['INVESTED'] * 100, 0)
    
    total_curr_value = df['CURR. VALUE'].sum()
    df['WT'] = np.where(total_curr_value != 0, df['CURR. VALUE'] / total_curr_value * 100, 0)
    df['WEIGHTED RETURN %'] = df['GAIN %'] * df['WT'] / 100
    
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


# ── Obsidian Quant chart theming helpers ────────────────────────────────────
def _apply_obsidian(fig, *, height: int = 360, show_legend: bool = False,
                    margin: dict | None = None, title: str = "",
                    x_title: str = "", y_title: str = "") -> None:
    """Apply Obsidian Quant Plotly theming (mutates fig in place)."""
    layout = chart_layout(height=height, show_legend=show_legend,
                          margin=margin or CHART_MARGIN)
    fig.update_layout(**layout)
    if title:
        fig.update_layout(
            title=dict(
                text=title,
                font=dict(size=11, color=CHART_INK_SUBTLE,
                          family="JetBrains Mono, monospace"),
                x=0, xanchor='left',
            )
        )
    style_axes(fig, y_title=y_title, x_title=x_title)


# Main app
def main() -> None:
    """Main application entry point."""
    # --- Sidebar Controls ---
    with st.sidebar:
        st.markdown(
            """
            <div style="text-align:center; padding: var(--sp-4) 0 var(--sp-3);">
                <div style="font-family: var(--display); font-size: 1.85rem; font-weight: 700;
                            letter-spacing: 0.04em; color: var(--amber);
                            text-shadow: 0 0 24px var(--amber-glow);">SAMHITA</div>
                <div style="font-family: var(--data); color: var(--ink-secondary);
                            font-size: 0.7rem; margin-top: var(--sp-1);
                            text-transform: uppercase; letter-spacing: 0.18em;">
                    संहिता · Portfolio Tracker
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-title">Data Controls</div>', unsafe_allow_html=True)
        if st.button("Refresh Prices", help="Clear cached prices and fetch fresh data"):
            st.cache_data.clear()
            # Re-arm the progress cards: the next run is a real (slow) cache
            # miss, so show loading feedback for both dashboard and analysis.
            st.session_state.pop('_samhita_dash_loaded', None)
            st.session_state.pop('_samhita_an_key', None)
            st.toast("Price cache cleared")
            st.rerun()

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-title">View Mode</div>', unsafe_allow_html=True)
        view_mode = st.radio(
            "Select View",
            ["Dashboard", "Analysis Mode"],
            label_visibility="collapsed",
        )

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-title">Anchor Date</div>', unsafe_allow_html=True)
        st.caption("Set a custom start date for Analysis Mode metrics")

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
            st.caption(f"Metrics calculated from {anchor_date.strftime('%b %d, %Y')}")

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-title">System</div>', unsafe_allow_html=True)
        st.markdown(
            f"""
            <div class="sys-meta">
                <div class="sys-meta-row">
                    <span class="sys-meta-key">Version</span>
                    <span class="sys-meta-val">{VERSION}</span>
                </div>
                <div class="sys-meta-row">
                    <span class="sys-meta-key">Data</span>
                    <span class="sys-meta-val">Yahoo Finance</span>
                </div>
                <div class="sys-meta-row">
                    <span class="sys-meta-key">Refresh</span>
                    <span class="sys-meta-val">5 min</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # Terminal masthead
    render_header(
        "Samhita",
        "संहिता · Portfolio Tracker · Real-Time Analytics & Performance Insights",
    )

    # Load data
    df = load_data()
    if df is None:
        return

    required_columns = ['ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE']
    if not all(col in df.columns for col in required_columns):
        st.error(
            f"Excel file must contain: {', '.join(required_columns)}. "
            "The 'CURRENT PRICE' column is now automatically fetched."
        )
        return

    # Themed progress card — shown on first dashboard load of the session
    # (prices are cached afterwards, so cosmetic reruns stay instant/quiet).
    _show_prog = not st.session_state.get('_samhita_dash_loaded', False)
    _prog_slot = st.empty() if _show_prog else None

    def _dash_progress(pct: int, label: str, sub: str = "") -> None:
        if _prog_slot is not None:
            progress_bar(_prog_slot, pct, label, sub)

    df, metrics = calculate_metrics(df, progress=_dash_progress)

    if _prog_slot is not None:
        progress_bar(_prog_slot, 100, "Portfolio Ready", f"{len(df)} holdings · prices live")
        _prog_slot.empty()
        st.session_state['_samhita_dash_loaded'] = True

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        render_metric_card(
            "Total Portfolio Value",
            format_currency(metrics['Total Current Value']),
            subtext=f"Invested: {format_currency(metrics['Total Invested'])}",
            color_class="warning",
        )

    with col2:
        gain_val = metrics['Total Gain']
        gain_sign = '+' if gain_val > 0 else ''
        render_metric_card(
            "Absolute Gain/Loss",
            f"{gain_sign}{format_currency(gain_val)}",
            subtext="Since inception",
            color_class="success" if gain_val >= 0 else "danger",
        )

    with col3:
        return_val = metrics['Portfolio Return %']
        return_sign = '+' if return_val > 0 else ''
        render_metric_card(
            "Total Return",
            f"{return_sign}{return_val:.2f}%",
            subtext="Portfolio XIRR equivalent",
            color_class="success" if return_val >= 0 else "danger",
        )

    with col4:
        today_val = metrics['Today Return %']
        today_change = metrics['Today Change']
        today_sign = '+' if today_val > 0 else ''
        change_sign = '+' if today_change > 0 else ''
        render_metric_card(
            "Today's Return",
            f"{today_sign}{today_val:.2f}%",
            subtext=f"{change_sign}{format_currency(today_change)}",
            color_class="success" if today_val >= 0 else "danger",
        )

    # =========================================================================
    # DASHBOARD VIEW (Default)
    # =========================================================================
    if view_mode == "Dashboard":
        tab1, tab2, tab3 = st.tabs(["Performance Analysis", "Portfolio Details", "Holdings Analytics"])

        with tab1:
            # ── Performance Snapshot ────────────────────────────────────────
            render_section_header(
                "Performance Snapshot",
                "Current portfolio performance summary · cost-basis returns",
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
                "Highest impact positions by absolute return and portfolio contribution",
                icon="trending",
                accent="cyan",
            )

            col_gainers, col_losers = st.columns(2)

            with col_gainers:
                render_section_header("Top Gainers", icon="trending", accent="emerald")
                top_5_gainers = df.nlargest(5, 'GAIN %')[['SYMBOL', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'GAIN']]
                fig_gainers = go.Figure()
                fig_gainers.add_trace(go.Bar(
                    y=top_5_gainers['SYMBOL'][::-1],
                    x=top_5_gainers['GAIN %'][::-1],
                    orientation='h',
                    marker_color=CHART_EMERALD,
                    text=[f"{x:+.1f}%" for x in top_5_gainers['GAIN %'][::-1]],
                    textposition='auto',
                    textfont=dict(size=11, color=CHART_INK),
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Weight: %{customdata[0]:.1f}%<br>Contribution: %{customdata[1]:.2f}%<extra></extra>",
                    customdata=top_5_gainers[['WT', 'WEIGHTED RETURN %']][::-1].values,
                ))
                _apply_obsidian(
                    fig_gainers, height=CHART_HEIGHT_SM, show_legend=False,
                    margin=CHART_MARGIN_BAR,
                    title="Absolute Return %",
                )
                st.plotly_chart(fig_gainers, width="stretch")

            with col_losers:
                render_section_header("Top Losers", icon="trending", accent="rose")
                top_5_losers = df.nsmallest(5, 'GAIN %')[['SYMBOL', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'GAIN']]
                fig_losers = go.Figure()
                fig_losers.add_trace(go.Bar(
                    y=top_5_losers['SYMBOL'],
                    x=top_5_losers['GAIN %'],
                    orientation='h',
                    marker_color=CHART_ROSE,
                    text=[f"{x:.1f}%" for x in top_5_losers['GAIN %']],
                    textposition='auto',
                    textfont=dict(size=11, color=CHART_INK),
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Weight: %{customdata[0]:.1f}%<br>Contribution: %{customdata[1]:.2f}%<extra></extra>",
                    customdata=top_5_losers[['WT', 'WEIGHTED RETURN %']].values,
                ))
                _apply_obsidian(
                    fig_losers, height=CHART_HEIGHT_SM, show_legend=False,
                    margin=CHART_MARGIN_BAR,
                    title="Absolute Return %",
                )
                st.plotly_chart(fig_losers, width="stretch")

            # ── Risk-Return Profile ─────────────────────────────────────────
            render_section_header(
                "Risk-Return Profile",
                "Position performance vs portfolio weight · bubble size = current value",
                icon="crosshair",
                accent="violet",
            )

            max_val = df['CURR. VALUE'].max()
            bubble_sizes = (df['CURR. VALUE'] / max_val * 40) + 10

            fig_scatter = go.Figure()
            fig_scatter.add_trace(go.Scatter(
                x=df['WT'],
                y=df['GAIN %'],
                mode='markers+text',
                marker=dict(
                    size=bubble_sizes,
                    color=df['GAIN %'],
                    colorscale=[[0, CHART_ROSE], [0.5, CHART_AMBER], [1, CHART_EMERALD]],
                    cmid=0,
                    line=dict(width=1, color="rgba(255,255,255,0.18)"),
                    opacity=0.85,
                ),
                text=df['SYMBOL'],
                textposition='top center',
                textfont=dict(size=9, color=CHART_INK),
                hovertemplate="<b>%{text}</b><br>Weight: %{x:.1f}%<br>Return: %{y:.2f}%<br>Value: ₹%{customdata:,.0f}<extra></extra>",
                customdata=df['CURR. VALUE'],
            ))

            fig_scatter.add_hline(y=0, line_dash="dash", line_color=CHART_INK_SUBTLE, line_width=1)
            avg_weight = df['WT'].mean()
            fig_scatter.add_vline(
                x=avg_weight, line_dash="dash", line_color=CHART_INK_SUBTLE, line_width=1,
                annotation_text=f"Avg Wt: {avg_weight:.1f}%", annotation_position="top",
            )

            _apply_obsidian(
                fig_scatter, height=CHART_HEIGHT_LG, show_legend=False,
                margin=CHART_MARGIN,
                title="Weight vs Return Matrix",
                x_title="Portfolio Weight (%)",
                y_title="Gain/Loss (%)",
            )
            st.plotly_chart(fig_scatter, width="stretch")

            # ── Return Attribution ──────────────────────────────────────────
            render_section_header(
                "Return Attribution",
                "Contribution of each holding to total portfolio return",
                icon="bar-chart",
            )

            contrib_sorted = df.sort_values('WEIGHTED RETURN %', ascending=False).copy()
            fig_waterfall = go.Figure()
            colors = [CHART_EMERALD if x >= 0 else CHART_ROSE for x in contrib_sorted['WEIGHTED RETURN %']]
            fig_waterfall.add_trace(go.Bar(
                x=contrib_sorted['SYMBOL'],
                y=contrib_sorted['WEIGHTED RETURN %'],
                marker_color=colors,
                text=[f"{x:+.2f}%" for x in contrib_sorted['WEIGHTED RETURN %']],
                textposition='auto',
                textfont=dict(size=10, color=CHART_INK),
                hovertemplate="<b>%{x}</b><br>Contribution: %{y:.3f}%<br>Return: %{customdata[0]:.1f}%<br>Weight: %{customdata[1]:.1f}%<extra></extra>",
                customdata=contrib_sorted[['GAIN %', 'WT']].values,
            ))
            _apply_obsidian(
                fig_waterfall, height=CHART_HEIGHT_LG, show_legend=False,
                margin=CHART_MARGIN_ROTATED,
                title="Weighted Return Contribution · sorted by impact",
                y_title="Contribution (%)",
            )
            fig_waterfall.update_xaxes(tickangle=45)
            st.plotly_chart(fig_waterfall, width="stretch")

            # ── Portfolio Composition ───────────────────────────────────────
            render_section_header(
                "Portfolio Composition",
                "Asset allocation by current value",
                icon="grid",
                accent="cyan",
            )

            min_gain_pct = df['GAIN %'].min()
            max_gain_pct = df['GAIN %'].max()
            color_scale_config: dict = {}
            if min_gain_pct >= 0:
                color_scale_config['color_continuous_scale'] = [CHART_AMBER, CHART_EMERALD]
                color_scale_config['range_color'] = [min_gain_pct, max_gain_pct]
            elif max_gain_pct <= 0:
                color_scale_config['color_continuous_scale'] = ["#F07075", CHART_ROSE]
                color_scale_config['range_color'] = [min_gain_pct, max_gain_pct]
            else:
                color_scale_config['color_continuous_scale'] = [CHART_ROSE, CHART_AMBER, CHART_EMERALD]
                color_scale_config['color_continuous_midpoint'] = 0

            fig_treemap = px.treemap(
                df,
                path=['SYMBOL'],
                values='CURR. VALUE',
                color='GAIN %',
                **color_scale_config,
            )
            fig_treemap.update_layout(
                margin=CHART_MARGIN_NOAXIS,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=PLOTLY_FONT,
                title=dict(
                    text="Value Allocation · color = Gain/Loss %",
                    font=dict(size=12, color=CHART_INK_SUBTLE, family="JetBrains Mono, monospace"),
                    x=0, xanchor='left',
                ),
                height=CHART_HEIGHT_LG,
            )
            st.plotly_chart(fig_treemap, width="stretch")

        with tab2:
            render_section_header(
                "Portfolio Holdings",
                "Detailed view of all investments · current price is near real-time",
                icon="database",
            )

            display_df = df[['ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE', 'INVESTED',
                             'CURRENT PRICE', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT']].copy()

            display_df['RANK'] = display_df['CURR. VALUE'].rank(ascending=False).astype(int)
            display_df = display_df.sort_values('RANK')

            display_df['AVERAGE PRICE'] = display_df['AVERAGE PRICE'].apply(format_currency)
            display_df['INVESTED'] = display_df['INVESTED'].apply(format_currency)
            display_df['CURRENT PRICE'] = display_df['CURRENT PRICE'].apply(format_currency)

            def format_gain(x):
                color = 'var(--emerald)' if x >= 0 else 'var(--rose)'
                return f"<span style='color:{color};font-weight:600;'>{format_currency(x)}</span>"

            def format_gain_pct(x):
                color = 'var(--emerald)' if x >= 0 else 'var(--rose)'
                return f"<span style='color:{color};font-weight:600;'>{x:.2f}%</span>"

            display_df['CURR. VALUE'] = display_df['CURR. VALUE'].apply(format_currency)
            display_df['GAIN'] = display_df['GAIN'].apply(format_gain)
            display_df['GAIN %'] = display_df['GAIN %'].apply(format_gain_pct)
            display_df['WT'] = display_df['WT'].apply(lambda x: f"{x:.2f}%")

            display_cols = ['RANK', 'ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE', 'CURRENT PRICE',
                            'INVESTED', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT']
            display_df = display_df[display_cols]

            table_html = display_df.to_html(
                escape=False,
                index=False,
                border=0,
                classes="portfolio-table",
            )
            st.markdown(f'<div class="portfolio-table">{table_html}</div>',
                        unsafe_allow_html=True)

            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

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
            returns = df['GAIN %'].values / 100

            hhi = (df['WT'] ** 2).sum()
            effective_n = 10000 / hhi if hhi > 0 else n_holdings
            gini = 0
            if n_holdings > 1:
                sorted_weights = np.sort(weights)
                cum_weights = np.cumsum(sorted_weights)
                gini = 1 - 2 * np.sum(cum_weights) / (n_holdings * cum_weights[-1]) if cum_weights[-1] > 0 else 0

            avg_weight = weights.mean()
            weight_std = weights.std()
            div_ratio = 1 / (hhi / 10000) if hhi > 0 else n_holdings

            render_section_header("Concentration Metrics", icon="layers", accent="cyan")
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

            render_section_header("Performance Distribution", icon="bar-chart", accent="emerald")
            c1, c2, c3, c4, c5, c6 = st.columns(6)

            profitable = (df['GAIN %'] > 0).sum()
            losing = (df['GAIN %'] < 0).sum()
            breakeven = n_holdings - profitable - losing
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
                render_section_header("Weight Distribution", icon="grid", accent="cyan")
                fig_tree = px.treemap(
                    df,
                    path=['SYMBOL'],
                    values='WT',
                    color='GAIN %',
                    color_continuous_scale=[CHART_ROSE, CHART_AMBER, CHART_EMERALD],
                    color_continuous_midpoint=0,
                )
                fig_tree.update_layout(
                    margin=CHART_MARGIN_NOAXIS,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    font=PLOTLY_FONT,
                    title=dict(text="Weight % · color = Gain/Loss",
                               font=dict(size=11, color=CHART_INK_SUBTLE, family="JetBrains Mono, monospace"),
                               x=0, xanchor='left'),
                    height=CHART_HEIGHT_MD,
                )
                fig_tree.update_coloraxes(showscale=False)
                st.plotly_chart(fig_tree, width="stretch")

            with col_lorenz:
                render_section_header("Concentration Curve", icon="activity", accent="violet")
                sorted_weights = np.sort(df['WT'].values)[::-1]
                cum_weights = np.cumsum(sorted_weights)
                n = len(sorted_weights)

                fig_lorenz = go.Figure()
                fig_lorenz.add_trace(go.Scatter(
                    x=list(range(n + 1)),
                    y=[0] + list(np.linspace(0, 100, n)),
                    mode='lines',
                    name='Equal Weight',
                    line=dict(color=CHART_INK_SUBTLE, dash='dash', width=1),
                ))
                fig_lorenz.add_trace(go.Scatter(
                    x=list(range(n + 1)),
                    y=[0] + list(cum_weights),
                    mode='lines+markers',
                    name='Portfolio',
                    line=dict(color=CHART_AMBER, width=2),
                    marker=dict(size=4),
                    fill='tonexty',
                    fillcolor=CHART_AMBER_GLOW,
                ))
                fig_lorenz.add_hline(y=50, line_dash="dot", line_color=CHART_EMERALD,
                                    annotation_text="50%", annotation_position="right")
                fig_lorenz.add_hline(y=80, line_dash="dot", line_color=CHART_CYAN,
                                    annotation_text="80%", annotation_position="right")
                _apply_obsidian(
                    fig_lorenz, height=CHART_HEIGHT_MD, show_legend=True,
                    margin=CHART_MARGIN,
                    title="Lorenz Curve · cumulative %",
                    x_title='# Holdings (ranked)',
                    y_title='Cumulative Weight (%)',
                )
                fig_lorenz.update_yaxes(range=[0, 105])
                st.plotly_chart(fig_lorenz, width="stretch")


            render_section_header("Risk & Return Contribution", icon="shield", accent="rose")

            contrib_df = df[['SYMBOL', 'ASSET NAME', 'WT', 'GAIN %', 'WEIGHTED RETURN %']].copy()
            contrib_df['Weight'] = contrib_df['WT'].apply(lambda x: f"{x:.2f}%")
            contrib_df['Return'] = contrib_df['GAIN %'].apply(lambda x: f"{x:+.2f}%")
            contrib_df['Contribution'] = contrib_df['WEIGHTED RETURN %'].apply(lambda x: f"{x:+.3f}%")
            contrib_df['Risk Weight'] = (contrib_df['WT'] ** 2) / hhi * 100
            contrib_df['Risk Contrib'] = contrib_df['Risk Weight'].apply(lambda x: f"{x:.1f}%")
            contrib_df = contrib_df.sort_values('WEIGHTED RETURN %', ascending=False)

            fig_contrib = make_subplots(rows=1, cols=2, shared_yaxes=True,
                                        subplot_titles=('Return Contribution', 'Risk Contribution'),
                                        horizontal_spacing=0.02)

            colors_ret = [CHART_EMERALD if x >= 0 else CHART_ROSE for x in contrib_df['WEIGHTED RETURN %']]

            fig_contrib.add_trace(go.Bar(
                y=contrib_df['SYMBOL'],
                x=contrib_df['WEIGHTED RETURN %'],
                orientation='h',
                marker_color=colors_ret,
                text=[f"{x:.2f}%" for x in contrib_df['WEIGHTED RETURN %']],
                textposition='auto',
                textfont=dict(size=9, color=CHART_INK),
                showlegend=False,
            ), row=1, col=1)

            fig_contrib.add_trace(go.Bar(
                y=contrib_df['SYMBOL'],
                x=contrib_df['Risk Weight'],
                orientation='h',
                marker_color=CHART_AMBER,
                text=[f"{x:.1f}%" for x in contrib_df['Risk Weight']],
                textposition='auto',
                textfont=dict(size=9, color=CHART_INK),
                showlegend=False,
            ), row=1, col=2)

            fig_contrib.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=PLOTLY_FONT,
                margin=CHART_MARGIN_BAR,
                height=max(CHART_HEIGHT_MD, n_holdings * 22 + 80),
                showlegend=False,
                hoverlabel=PLOTLY_HOVERLABEL,
            )

            fig_contrib.update_xaxes(gridcolor=CHART_GRID, zeroline=False,
                                     tickfont=dict(size=9, family="JetBrains Mono, monospace",
                                                   color=CHART_INK_SUBTLE))
            fig_contrib.update_yaxes(gridcolor=CHART_GRID, zeroline=False,
                                     tickfont=dict(size=9, family="JetBrains Mono, monospace",
                                                   color=CHART_INK_SUBTLE))

            st.plotly_chart(fig_contrib, width="stretch")
            
            # Summary Statistics in expander
            with st.expander("Detailed Statistics", expanded=False):
                col_s1, col_s2, col_s3, col_s4 = st.columns(4)
                
                with col_s1:
                    st.markdown("**Weight Stats**")
                    st.markdown(f"""
                    - Mean: **{df['WT'].mean():.2f}%**
                    - Median: **{df['WT'].median():.2f}%**
                    - Std: **{df['WT'].std():.2f}%**
                    - Max: **{df['WT'].max():.2f}%**
                    - Min: **{df['WT'].min():.2f}%**
                    """)
                
                with col_s2:
                    st.markdown("**Return Stats**")
                    st.markdown(f"""
                    - Mean: **{df['GAIN %'].mean():.2f}%**
                    - Median: **{df['GAIN %'].median():.2f}%**
                    - Std: **{df['GAIN %'].std():.2f}%**
                    - Max: **{df['GAIN %'].max():.2f}%**
                    - Min: **{df['GAIN %'].min():.2f}%**
                    """)
                
                with col_s3:
                    st.markdown("**Concentration**")
                    st.markdown(f"""
                    - Top 1: **{df['WT'].max():.1f}%**
                    - Top 3: **{df['WT'].nlargest(3).sum():.1f}%**
                    - Top 5: **{df['WT'].nlargest(5).sum():.1f}%**
                    - Top 10: **{df['WT'].nlargest(10).sum():.1f}%**
                    - Bottom 50%: **{df['WT'].nsmallest(n_holdings//2).sum():.1f}%**
                    """)
                
                with col_s4:
                    st.markdown("**Diversification**")
                    st.markdown(f"""
                    - HHI: **{hhi:.0f}**
                    - Effective N: **{effective_n:.1f}**
                    - Gini: **{gini:.3f}**
                    - Div Ratio: **{div_ratio:.2f}**
                    - Entropy: **{-np.sum(weights * np.log(weights + 1e-10)):.2f}**
                    """)
    
    # =========================================================================
    # ANALYSIS MODE
    # =========================================================================
    if view_mode == "Analysis Mode":
        render_analysis_mode(df, metrics, anchor_date)
    
    # ── Footer ──────────────────────────────────────────────────────────────
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    current_time_ist = ist_now.strftime("%Y-%m-%d %H:%M:%S IST")
    st.markdown(
        f"""
        <div style="display:flex; justify-content:space-between; align-items:center;
                    font-family: var(--data); font-size: 0.72rem;
                    color: var(--ink-tertiary); padding: var(--sp-3) 0;
                    text-transform: uppercase; letter-spacing: 0.14em;">
            <span>© 2026 {PRODUCT_NAME} · {COMPANY}</span>
            <span>{VERSION} · {current_time_ist}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


# =========================================================================
# ANALYSIS MODE - INSTITUTIONAL GRADE ANALYTICS
# =========================================================================

BENCHMARK_TICKER = '^NSEI'  # NIFTY 50 only
BENCHMARK_NAME = 'NIFTY 50'

TIMEFRAMES = {
    '1W': 7,
    '1M': 30,
    '3M': 90,
    '6M': 180,
    'YTD': None,  # Special handling
    '1Y': 365,
    '2Y': 730,
    '5Y': 1825,
    'MAX': 3650
}

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
    rf_rate: float = 0.065,
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
    
    # Annualization factor - cap at 1 for very short periods
    ann_factor = min(252 / n_days, 1) if n_days < 252 else 252 / n_days
    
    m['total_return'] = total_ret * 100
    
    # CAGR calculation - handle negative returns properly
    if total_ret > -1:  # Can only compute if not total loss
        # For short periods, just annualize the total return
        if n_days < 20:
            m['cagr'] = total_ret * (252 / n_days) * 100  # Simple annualization
        else:
            m['cagr'] = ((1 + total_ret) ** ann_factor - 1) * 100
    else:
        m['cagr'] = -100  # Total loss
    
    # Volatility
    daily_vol = returns.std()
    m['volatility'] = daily_vol * np.sqrt(252) * 100 if daily_vol > 0 else 0
    m['daily_vol'] = daily_vol * 100
    
    # Drawdown
    cum = (1 + returns).cumprod()
    peak = cum.expanding().max()
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
    
    # Sortino - use downside deviation
    downside = returns[returns < 0]
    if len(downside) > 0:
        downside_vol = downside.std()
        if downside_vol > 1e-8:
            m['sortino'] = (excess_mean / downside_vol) * np.sqrt(252)
        else:
            m['sortino'] = m['sharpe']  # Fall back to Sharpe
    else:
        # No negative days - exceptional performance
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
            
            # Alpha (annualized) - CAPM formula
            aligned_days = len(aligned)
            aligned_ann = min(252 / aligned_days, 1) if aligned_days < 252 else 252 / aligned_days
            
            if b_total > -1:
                b_cagr = ((1 + b_total) ** aligned_ann - 1) if aligned_days >= 20 else b_total * (252 / aligned_days)
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
            
            if up_mask.sum() > 0:
                up_p = (1 + p_ret[up_mask]).prod()
                up_b = (1 + b_ret[up_mask]).prod()
                if up_b > 0:
                    m['up_capture'] = (up_p / up_b) * 100
            
            if down_mask.sum() > 0:
                down_p = (1 + p_ret[down_mask]).prod()
                down_b = (1 + b_ret[down_mask]).prod()
                if down_b > 0 and down_b != 1:
                    m['down_capture'] = (down_p / down_b) * 100
    
    return m


def render_analysis_mode(
    df: pd.DataFrame, metrics: dict[str, float], anchor_date: datetime | None = None
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
    
    # Timeframe buttons row (disabled when anchor date is active)
    if anchor_date:
        st.toast(f"Anchor date active · metrics from {anchor_date.strftime('%b %d, %Y')}")
        days_back = (datetime.now().date() - anchor_date).days + 1
        selected_tf = "CUSTOM"
        
        # Still show timeframe buttons but disabled style
        tf_cols = st.columns(len(TIMEFRAMES))
        for i, tf in enumerate(TIMEFRAMES.keys()):
            with tf_cols[i]:
                st.button(tf, key=f"tf_{tf}_disabled", width="stretch", disabled=True)
    else:
        tf_cols = st.columns(len(TIMEFRAMES))
        for i, tf in enumerate(TIMEFRAMES.keys()):
            with tf_cols[i]:
                btn_type = "primary" if st.session_state.tf_selected == tf else "secondary"
                if st.button(tf, key=f"tf_{tf}", width="stretch", type=btn_type):
                    st.session_state.tf_selected = tf
                    st.rerun()
        
        # Calculate days for selected timeframe
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
    _show_prog = st.session_state.get('_samhita_an_key') != _an_key
    _prog_slot = st.empty() if _show_prog else None
    if _prog_slot is not None:
        progress_bar(_prog_slot, 30, "Fetching analysis history",
                     f"yfinance · {len(symbols)} holdings + NIFTY 50")

    portfolio_prices, benchmark_prices = fetch_analysis_data(symbols, days_back)

    if _prog_slot is not None:
        progress_bar(_prog_slot, 100, "History Ready",
                     f"{selected_tf} · {len(portfolio_prices)} trading days")
        _prog_slot.empty()
        st.session_state['_samhita_an_key'] = _an_key
    
    if portfolio_prices.empty:
        st.error("Unable to fetch historical data. Please try again.")
        return
    
    # Apply anchor date filter if set
    if anchor_date:
        anchor_datetime = pd.Timestamp(anchor_date)
        portfolio_prices = portfolio_prices[portfolio_prices.index >= anchor_datetime]
        benchmark_prices = benchmark_prices[benchmark_prices.index >= anchor_datetime]
        
        if portfolio_prices.empty:
            st.warning(f"No data available from {anchor_date.strftime('%b %d, %Y')}. Try an earlier anchor date.")
            return
    
    # Build portfolio value series (already aligned to NIFTY 50 dates)
    port_value = pd.DataFrame(index=portfolio_prices.index)
    for sym in portfolio_prices.columns:
        if sym in quantities:
            port_value[sym] = portfolio_prices[sym] * quantities[sym]
    port_value['Portfolio'] = port_value.sum(axis=1)
    port_value = port_value['Portfolio'].dropna()
    
    # Calculate returns
    port_returns = port_value.pct_change(fill_method=None).dropna()
    
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
        line=dict(color=CHART_AMBER, width=2.5),
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
                line=dict(color=CHART_CYAN, width=2, dash='dot'),
                hovertemplate=f'%{{x|%b %d, %Y}}<br>{BENCHMARK_NAME}: %{{y:.2f}}<extra></extra>',
            ))

    _apply_obsidian(
        fig, height=CHART_HEIGHT_LG, show_legend=True,
        margin=CHART_MARGIN_NOTITLE,
    )
    fig.update_yaxes(side='right')
    fig.update_layout(hovermode='closest')
    fig.update_xaxes(rangeslider=dict(visible=False), rangeselector=dict(visible=False))

    st.plotly_chart(fig, width="stretch", config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d'],
    })

    # ── Returns & Risk-Adjusted Performance ─────────────────────────────────
    render_section_header("Returns & Risk-Adjusted Performance", icon="zap", accent="emerald")
    c1, c2, c3, c4, c5, c6 = st.columns(6)

    with c1:
        val = m.get('total_return', 0)
        render_metric_card("Period Return", f"{val:+.2f}%",
                           subtext=f"CAGR: {m.get('cagr', 0):+.1f}%",
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
    render_section_header("Risk Metrics", icon="shield", accent="rose")
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
    render_section_header("Benchmark Comparison", icon="compass", accent="cyan")
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
        render_section_header("Drawdown Analysis", icon="activity", accent="rose")
        dd_series = m.get('drawdown_series', pd.Series())
        if len(dd_series) > 0:
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=dd_series.index,
                y=dd_series.values,
                mode='lines',
                fill='tozeroy',
                line=dict(color=CHART_ROSE, width=1),
                fillcolor='rgba(232, 85, 90, 0.25)',
                hovertemplate='%{x|%b %d, %Y}<br>Drawdown: %{y:.2f}%<extra></extra>',
            ))
            fig_dd.add_hline(
                y=m.get('max_drawdown', 0),
                line_dash="dash",
                line_color=CHART_AMBER,
                annotation_text=f"Max: {m.get('max_drawdown', 0):.1f}%",
                annotation_position="right",
            )
            _apply_obsidian(
                fig_dd, height=CHART_HEIGHT_MD, show_legend=False,
                margin=CHART_MARGIN,
                title="Underwater Equity Curve",
            )
            st.plotly_chart(fig_dd, width="stretch")

    with col_dist:
        render_section_header("Returns Distribution", icon="bar-chart", accent="emerald")
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=port_returns * 100,
            nbinsx=40,
            marker_color=CHART_AMBER,
            opacity=0.78,
            hovertemplate='Return: %{x:.2f}%<br>Count: %{y}<extra></extra>',
        ))
        fig_hist.add_vline(x=0, line_dash="dash", line_color=CHART_INK_SUBTLE, line_width=1)
        fig_hist.add_vline(
            x=port_returns.mean() * 100,
            line_dash="dot",
            line_color=CHART_EMERALD,
            annotation_text=f"μ: {port_returns.mean()*100:.2f}%",
            annotation_position="top",
        )
        fig_hist.add_vline(
            x=m.get('var_95', 0),
            line_dash="dash",
            line_color=CHART_ROSE,
            annotation_text=f"VaR: {m.get('var_95', 0):.1f}%",
            annotation_position="bottom left",
        )
        _apply_obsidian(
            fig_hist, height=CHART_HEIGHT_MD, show_legend=False,
            margin=CHART_MARGIN,
            title="Daily Returns Histogram",
            x_title='Daily Return (%)',
        )
        st.plotly_chart(fig_hist, width="stretch")
    
    # ── Rolling Analytics (dynamic window based on timeframe) ───────────────
    data_length = len(port_returns)

    if data_length < 15:
        pass
    else:
        rolling_window = min(63, max(10, data_length // 3))

        render_section_header(
            "Rolling Analytics",
            f"{rolling_window}-day rolling window",
            icon="activity",
            accent="violet",
        )

        col_rs, col_rb = st.columns(2)

        with col_rs:
            roll_mean = port_returns.rolling(rolling_window).mean()
            roll_std = port_returns.rolling(rolling_window).std()
            roll_sharpe = (roll_mean / roll_std) * np.sqrt(252)
            roll_sharpe = roll_sharpe.dropna()

            if len(roll_sharpe) > 0:
                fig_rs = go.Figure()
                fig_rs.add_trace(go.Scatter(
                    x=roll_sharpe.index,
                    y=roll_sharpe.values,
                    mode='lines',
                    line=dict(color=CHART_AMBER, width=1.5),
                    hovertemplate='%{x|%b %d, %Y}<br>Sharpe: %{y:.2f}<extra></extra>',
                ))
                fig_rs.add_hline(y=1, line_dash="dash", line_color=CHART_EMERALD,
                                 annotation_text="Target", annotation_position="right")
                fig_rs.add_hline(y=0, line_dash="dash", line_color=CHART_INK_SUBTLE)
                _apply_obsidian(
                    fig_rs, height=CHART_HEIGHT_SM, show_legend=False,
                    margin=CHART_MARGIN,
                    title="Rolling Sharpe Ratio",
                )
                fig_rs.update_xaxes(tickformat='%b %Y')
                st.plotly_chart(fig_rs, width="stretch")

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
                            line=dict(color=CHART_CYAN, width=1.5),
                            hovertemplate='%{x|%b %d, %Y}<br>Beta: %{y:.2f}<extra></extra>',
                        ))
                        fig_rb.add_hline(y=1, line_dash="dash", line_color=CHART_INK_SUBTLE,
                                         annotation_text="Market", annotation_position="right")
                        _apply_obsidian(
                            fig_rb, height=CHART_HEIGHT_SM, show_legend=False,
                            margin=CHART_MARGIN,
                            title=f"Rolling Beta vs {BENCHMARK_NAME}",
                        )
                        fig_rb.update_xaxes(tickformat='%b %Y')
                        st.plotly_chart(fig_rb, width="stretch")

    # ── Monthly Returns Heatmap ─────────────────────────────────────────────
    render_section_header("Monthly Returns Heatmap", icon="grid", accent="emerald")
    
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
            
            # Calculate YTD for this year
            year_start_val = port_value[port_value.index.year == year].iloc[0] if len(port_value[port_value.index.year == year]) > 0 else np.nan
            year_end_val = port_value[port_value.index.year == year].iloc[-1] if len(port_value[port_value.index.year == year]) > 0 else np.nan
            if pd.notna(year_start_val) and pd.notna(year_end_val) and year_start_val > 0:
                ytd = ((year_end_val / year_start_val) - 1) * 100
            else:
                ytd = np.nan
            row.append(ytd)
            
            heatmap_data.append(row)
            year_labels.append(str(year))
        
        # Column labels
        col_labels = month_names + ['YTD']
        
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=col_labels,
            y=year_labels,
            colorscale=[[0, CHART_ROSE], [0.5, "#0A0E17"], [1, CHART_EMERALD]],
            zmid=0,
            text=[[f"{v:.1f}%" if pd.notna(v) else "" for v in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont=dict(size=10, color=CHART_INK, family="JetBrains Mono, monospace"),
            hovertemplate="Year: %{y}<br>%{x}: %{z:.2f}%<extra></extra>",
            showscale=False,
        ))

        fig_heat.update_layout(
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=PLOTLY_FONT,
            margin=CHART_MARGIN_HEATMAP,
            title=dict(
                text="Month-over-Month Returns (%)",
                font=dict(size=12, color=CHART_INK_SUBTLE, family="JetBrains Mono, monospace"),
                x=0, xanchor='left',
            ),
            xaxis=dict(side='top', tickangle=0, type='category', dtick=1,
                       tickfont=dict(size=9, family="JetBrains Mono, monospace",
                                     color=CHART_INK_SUBTLE)),
            yaxis=dict(autorange='reversed', type='category', dtick=1,
                       tickfont=dict(size=9, family="JetBrains Mono, monospace",
                                     color=CHART_INK_SUBTLE)),
            height=max(CHART_HEIGHT_SM, len(years) * 38 + 80),
            hoverlabel=PLOTLY_HOVERLABEL,
        )

        st.plotly_chart(fig_heat, width="stretch")

    # ── Holding Attribution ─────────────────────────────────────────────────
    render_section_header("Holding Attribution", icon="link", accent="cyan")

    attribution = []
    for sym in symbols:
        if sym in portfolio_prices.columns:
            prices = portfolio_prices[sym].dropna()
            if len(prices) > 1:
                ret = (prices.iloc[-1] / prices.iloc[0] - 1) * 100
                wt = df[df['SYMBOL'] == sym]['WT'].values[0] if 'WT' in df.columns else 0
                contrib = ret * wt / 100
                attribution.append({
                    'Symbol': sym,
                    'Return': ret,
                    'Weight': wt,
                    'Contribution': contrib,
                })

    if attribution:
        attr_df = pd.DataFrame(attribution).sort_values('Contribution', ascending=True)
        fig_attr = go.Figure()
        colors = [CHART_EMERALD if x >= 0 else CHART_ROSE for x in attr_df['Contribution']]
        fig_attr.add_trace(go.Bar(
            y=attr_df['Symbol'],
            x=attr_df['Contribution'],
            orientation='h',
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in attr_df['Contribution']],
            textposition='auto',
            textfont=dict(size=10, color=CHART_INK),
            hovertemplate="<b>%{y}</b><br>Return: %{customdata[0]:.1f}%<br>Weight: %{customdata[1]:.1f}%<br>Contribution: %{x:.2f}%<extra></extra>",
            customdata=attr_df[['Return', 'Weight']].values,
        ))
        _apply_obsidian(
            fig_attr, height=max(CHART_HEIGHT_MD, len(attr_df) * 25 + 70), show_legend=False,
            margin=CHART_MARGIN_BAR,
            title="Contribution to Portfolio Return (%)",
        )
        st.plotly_chart(fig_attr, width="stretch")
    
    # =========================================================================
    # STATISTICS TABLE
    # =========================================================================
    
    
    with st.expander("Detailed Statistics", expanded=False):
        col_s1, col_s2, col_s3 = st.columns(3)
        
        with col_s1:
            st.markdown("**Performance**")
            st.markdown(f"""
            - Total Return: **{m.get('total_return', 0):+.2f}%**
            - CAGR: **{m.get('cagr', 0):+.2f}%**
            - Best Day: **{m.get('best_day', 0):+.2f}%**
            - Worst Day: **{m.get('worst_day', 0):.2f}%**
            - Win Rate: **{m.get('win_rate', 0):.1f}%** ({m.get('win_days', 0)}W / {m.get('lose_days', 0)}L)
            - Profit Factor: **{m.get('profit_factor', 0):.2f}**
            """)
        
        with col_s2:
            st.markdown("**Risk**")
            st.markdown(f"""
            - Volatility (Ann.): **{m.get('volatility', 0):.2f}%**
            - Daily Volatility: **{m.get('daily_vol', 0):.3f}%**
            - Max Drawdown: **{m.get('max_drawdown', 0):.2f}%**
            - VaR 95%: **{m.get('var_95', 0):.2f}%**
            - VaR 99%: **{m.get('var_99', 0):.2f}%**
            - CVaR 95%: **{m.get('cvar_95', 0):.2f}%**
            """)
        
        with col_s3:
            st.markdown("**Distribution**")
            st.markdown(f"""
            - Skewness: **{m.get('skewness', 0):.3f}**
            - Kurtosis: **{m.get('kurtosis', 0):.3f}**
            - Sharpe: **{m.get('sharpe', 0):.2f}**
            - Sortino: **{m.get('sortino', 0):.2f}**
            - Calmar: **{m.get('calmar', 0):.2f}**
            - Treynor: **{m.get('treynor', 0):.3f}**
            """)
    
    st.toast(f"Analytics loaded for {selected_tf}")


if __name__ == "__main__":
    main()
