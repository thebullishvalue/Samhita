# -*- coding: utf-8 -*-
"""
SAMHITA (संहिता) - Portfolio Tracker | A @thebullishvalue Product
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Real-time ETF portfolio analytics with performance tracking.
Time series analysis and historical performance insights.
"""

from __future__ import annotations

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

# --- Constants ---
VERSION = "v1.1.1"
PRODUCT_NAME = "Samhita"
COMPANY = "@thebullishvalue"

# Streamlit page configuration
st.set_page_config(
    page_title="SAMHITA | Portfolio Tracker",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="collapsed"
)

# --- Premium Professional CSS (@thebullishvalue Design System) ---
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            --primary-color: #FFC300;
            --primary-rgb: 255, 195, 0;
            --background-color: #0F0F0F;
            --secondary-background-color: #1A1A1A;
            --bg-card: #1A1A1A;
            --bg-elevated: #2A2A2A;
            --text-primary: #EAEAEA;
            --text-secondary: #EAEAEA;
            --text-muted: #888888;
            --border-color: #2A2A2A;
            --border-light: #3A3A3A;
            
            --success-green: #10b981;
            --success-dark: #059669;
            --danger-red: #ef4444;
            --danger-dark: #dc2626;
            --warning-amber: #f59e0b;
            --info-cyan: #06b6d4;
            
            --neutral: #888888;
        }
        
        * {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }
        
        .main, [data-testid="stSidebar"] {
            background-color: var(--background-color);
            color: var(--text-primary);
        }
        
        .stApp > header {
            background-color: transparent;
        }
        
        #MainMenu {visibility: hidden;} footer {visibility: hidden;}
        
        .block-container {
            padding-top: 3.5rem;
            max-width: 90%; 
            padding-left: 2rem; 
            padding-right: 2rem;
        }
        
        /* Sidebar toggle button - always visible */
        [data-testid="collapsedControl"] {
            display: flex !important;
            visibility: visible !important;
            opacity: 1 !important;
            background-color: var(--secondary-background-color) !important;
            border: 2px solid var(--primary-color) !important;
            border-radius: 8px !important;
            padding: 10px !important;
            margin: 12px !important;
            box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.4) !important;
            z-index: 999999 !important;
            position: fixed !important;
            top: 14px !important;
            left: 14px !important;
            width: 40px !important;
            height: 40px !important;
            align-items: center !important;
            justify-content: center !important;
        }
        
        [data-testid="collapsedControl"]:hover {
            background-color: rgba(var(--primary-rgb), 0.2) !important;
            box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.6) !important;
            transform: scale(1.05);
        }
        
        [data-testid="collapsedControl"] svg {
            stroke: var(--primary-color) !important;
            width: 20px !important;
            height: 20px !important;
        }
        
        [data-testid="stSidebar"] button[kind="header"] {
            background-color: transparent !important;
            border: none !important;
        }
        
        [data-testid="stSidebar"] button[kind="header"] svg {
            stroke: var(--primary-color) !important;
        }
        
        button[kind="header"] {
            z-index: 999999 !important;
        }
        
        [data-testid="stSidebar"] { 
            background: var(--secondary-background-color); 
            border-right: 1px solid var(--border-color); 
        }
        
        /* Premium Header Structure */
        .premium-header {
            background: var(--secondary-background-color);
            padding: 1.25rem 2rem;
            border-radius: 16px;
            margin-bottom: 1.5rem;
            box-shadow: 0 0 20px rgba(var(--primary-rgb), 0.1);
            border: 1px solid var(--border-color);
            position: relative;
            overflow: hidden;
            margin-top: 1rem;
        }
        
        .premium-header::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: radial-gradient(circle at 20% 50%, rgba(var(--primary-rgb),0.08) 0%, transparent 50%);
            pointer-events: none;
        }
        
        .premium-header h1 {
            margin: 0;
            font-size: 2rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.50px;
            position: relative;
        }
        
        .premium-header .tagline {
            color: var(--text-muted);
            font-size: 0.9rem;
            margin-top: 0.25rem;
            font-weight: 400;
            position: relative;
        }
        
        /* Metric Card Styling */
        .metric-card {
            background-color: var(--bg-card);
            padding: 1.25rem;
            border-radius: 12px;
            border: 1px solid var(--border-color);
            box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.08);
            margin-bottom: 0.5rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            height: 100%;
        }
        
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 30px rgba(0,0,0,0.3);
            border-color: var(--border-light);
        }
        
        .metric-card h4 {
            color: var(--text-muted);
            font-size: 0.75rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-card h2 {
            color: var(--text-primary);
            font-size: 1.75rem;
            font-weight: 700;
            margin: 0;
            line-height: 1;
        }
        
        .metric-card .sub-metric {
            font-size: 0.75rem;
            color: var(--text-muted);
            margin-top: 0.5rem;
            font-weight: 500;
        }
        
        .metric-card.success h2 { color: var(--success-green); }
        .metric-card.danger h2 { color: var(--danger-red); }
        .metric-card.warning h2 { color: var(--warning-amber); }
        .metric-card.info h2 { color: var(--info-cyan); }
        .metric-card.neutral h2 { color: var(--neutral); }
        .metric-card.primary h2 { color: var(--primary-color); }

        /* Performance Card (for Highlights) */
        .performance-card {
            padding: 0.75rem; 
            border-radius: 6px;
            margin-bottom: 0.75rem; 
            background: var(--bg-elevated);
            border-left: 3px solid;
            transition: background 0.2s;
        }
        .performance-card:hover {
            background: var(--border-color);
        }
        
        .performance-card.positive { border-left-color: var(--success-green); }
        .performance-card.negative { border-left-color: var(--danger-red); }
        
        .performance-card .title {
            font-weight: 600;
            font-size: 1rem; 
            margin-bottom: 0.3rem;
            color: var(--text-primary);
        }
        
        .performance-card .stats {
            display: flex;
            justify-content: space-between;
            font-size: 0.85rem; 
            color: var(--text-primary);
            font-weight: 500;
            margin-bottom: 0.2rem;
        }

        .performance-section-header {
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--text-primary);
            margin-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 5px;
        }

        .performance-subheader {
            font-size: 0.95rem;
            font-weight: 500;
            color: var(--text-muted);
            margin-bottom: 0.5rem;
        }
        
        /* Table Styling */
        .table-container {
            width: 100%;
            overflow-x: auto;
            border-radius: 12px;
            background: var(--bg-card);
            border: 1px solid var(--border-color);
            box-shadow: 0 4px 20px rgba(0,0,0,0.2);
            padding: 0;
        }
        
        table.table {
            width: 100%;
            table-layout: auto;
            border-collapse: collapse;
            color: var(--text-primary);
        }
        
        table.table th, table.table td {
            padding: 1rem 1.2rem;
            text-align: left;
            border-bottom: 1px solid var(--border-color);
        }
        
        table.table th {
            font-weight: 600;
            color: var(--primary-color);
            background-color: var(--bg-elevated);
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.05em;
        }
        
        table.table td {
            font-size: 0.95rem;
        }
        
        table.table tr:hover {
            background: var(--bg-elevated);
        }

        /* Tab styling */
        .stTabs [data-baseweb="tab-list"] {
            gap: 24px;
            background: transparent;
            padding: 0;
            margin-top: 1.5rem;
            margin-bottom: 1.5rem;
        }
        
        .stTabs [data-baseweb="tab"] {
            color: var(--text-muted);
            border-bottom: 2px solid transparent;
            transition: color 0.3s, border-bottom 0.3s;
            background: transparent;
            font-weight: 600;
        }
        
        .stTabs [aria-selected="true"] {
            color: var(--primary-color) !important;
            border-bottom: 2px solid var(--primary-color);
            background: transparent !important;
        }
        
        /* Utility classes */
        .positive { color: var(--success-green) !important; }
        .negative { color: var(--danger-red) !important; }
        .neutral { color: var(--text-primary) !important; }

        /* General Section Dividers/Headers */
        .section-header {
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .section-title {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--text-primary);
            margin: 0;
        }
        
        .section-subtitle {
            font-size: 0.95rem;
            color: var(--text-muted);
            margin: 0.25rem 0 0 0;
        }

        .section-divider {
            height: 1px;
            background: linear-gradient(90deg, transparent 0%, var(--border-color) 50%, transparent 100%);
            margin: 1.5rem 0;
        }
        
        .sidebar-title { 
            font-size: 0.75rem; 
            font-weight: 700; 
            color: var(--primary-color); 
            text-transform: uppercase; 
            letter-spacing: 1px; 
            margin-bottom: 0.75rem; 
        }
        
        .info-box { 
            background: var(--secondary-background-color); 
            border: 1px solid var(--border-color); 
            padding: 1.25rem; 
            border-radius: 12px; 
            margin: 0.5rem 0; 
            box-shadow: 0 0 15px rgba(var(--primary-rgb), 0.08); 
        }
        .info-box h4 { color: var(--primary-color); margin: 0 0 0.5rem 0; font-size: 1rem; font-weight: 700; }
        .info-box p { color: var(--text-muted); margin: 0; font-size: 0.9rem; line-height: 1.6; }

        /* Buttons - Gold outline with glow on hover */
        .stButton>button {
            border: 2px solid var(--primary-color);
            background: transparent;
            color: var(--primary-color);
            font-weight: 700;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stButton>button:hover {
            box-shadow: 0 0 25px rgba(var(--primary-rgb), 0.6);
            background: var(--primary-color);
            color: #1A1A1A;
            transform: translateY(-2px);
        }
        
        .stButton>button:active {
            transform: translateY(0);
        }

        /* Download button styling */
        .stDownloadButton>button {
            border: 2px solid var(--primary-color);
            background: transparent;
            color: var(--primary-color);
            font-weight: 700;
            border-radius: 12px;
            padding: 0.75rem 2rem;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .stDownloadButton>button:hover {
            box-shadow: 0 0 25px rgba(var(--primary-rgb), 0.6);
            background: var(--primary-color);
            color: #1A1A1A;
            transform: translateY(-2px);
        }
        
        .stPlotlyChart {
            border-radius: 12px;
            background-color: var(--secondary-background-color);
            padding: 10px;
            border: 1px solid var(--border-color);
            box-shadow: 0 0 25px rgba(var(--primary-rgb), 0.1);
        }
        
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: var(--background-color); }
        ::-webkit-scrollbar-thumb { background: var(--border-color); border-radius: 3px; }
        ::-webkit-scrollbar-thumb:hover { background: var(--border-light); }
    </style>
    """, unsafe_allow_html=True)

load_css()

# Function to fetch current prices from yfinance
@st.cache_data(ttl=300, show_spinner="Fetching real-time prices...")  # 5 min cache
def fetch_current_prices(symbols: list[str]) -> dict[str, float | Any]:
    """
    Fetches the latest closing price for a list of symbols with the .NS suffix.
    Returns a dictionary of {original_symbol: price}.

    Uses the same proven approach as returns.py:
    - Daily data (no intraday interval) to avoid rate limits
    - Single bulk download for all tickers
    - 5-day period to handle weekends/holidays
    """
    if not symbols:
        return {}

    # Add .NS suffix to symbols
    tickers_with_suffix = [f"{s}.NS" for s in symbols if s and isinstance(s, str)]
    
    prices = {}
    
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
            st.warning("yfinance returned empty data.")
            return {s: np.nan for s in symbols}
        
        # Get Close prices
        try:
            close_prices = data['Close']
        except KeyError:
            st.warning("No 'Close' column in fetched data.")
            return {s: np.nan for s in symbols}
        
        if close_prices.empty:
            return {s: np.nan for s in symbols}
        
        # Single ticker case: close_prices is a Series
        if len(tickers_with_suffix) == 1:
            ticker = tickers_with_suffix[0]
            original = ticker.replace('.NS', '')
            last_price = close_prices.dropna().iloc[-1] if not close_prices.dropna().empty else np.nan
            prices[original] = float(last_price) if not pd.isna(last_price) else np.nan
        
        # Multiple tickers case: close_prices is a DataFrame
        else:
            # Get last row (most recent date)
            latest_prices = close_prices.iloc[-1]
            
            for ticker in tickers_with_suffix:
                original = ticker.replace('.NS', '')
                try:
                    price = latest_prices[ticker]
                    prices[original] = float(price) if not pd.isna(price) else np.nan
                except (KeyError, TypeError):
                    prices[original] = np.nan
                    
    except Exception as e:
        st.error(f"Error fetching data from yfinance: {e}")
        return {s: np.nan for s in symbols}
    
    # Report any failures
    failed = [s for s in symbols if s in prices and pd.isna(prices.get(s))]
    if failed:
        st.warning(f"⚠️ Could not fetch prices for: {', '.join(failed[:5])}{'...' if len(failed) > 5 else ''}")
    
    return prices
    

# Function to load data
@st.cache_data
def load_data() -> pd.DataFrame | None:
    """Load portfolio data from Excel file."""
    file_path = "ETF Summary Report.xlsx"
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        st.error(f"File '{file_path}' not found. Please upload the data file.")
        return None

# Function to fetch previous day close prices for Today Return calculation
@st.cache_data(ttl=300)
def fetch_previous_close(symbols: list[str]) -> dict[str, float | Any]:
    """Fetch previous trading day close prices for calculating today return."""
    if not symbols:
        return {}
    
    prices = {}
    tickers_with_suffix = [f"{s}.NS" for s in symbols]
    
    try:
        # Fetch 5 days of data to ensure we get previous close
        data = yf.download(
            tickers=tickers_with_suffix,
            period='5d',
            interval='1d',
            progress=False,
            threads=True
        )
        
        if data.empty:
            return {s: np.nan for s in symbols}
        
        close_prices = data['Close']
        
        # Single ticker case
        if len(tickers_with_suffix) == 1:
            ticker = tickers_with_suffix[0]
            original = ticker.replace('.NS', '')
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
                    original = ticker.replace('.NS', '')
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
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Calculate portfolio performance metrics."""
    df = df.copy()
    symbols = df['SYMBOL'].tolist()
    price_map = fetch_current_prices(symbols)
    
    # 2. Fetch previous close for today's return
    prev_close_map = fetch_previous_close(symbols)
    
    # 3. Update CURRENT PRICE column using fetched data
    df['FETCHED PRICE'] = df['SYMBOL'].map(price_map)
    df['CURRENT PRICE'] = df['FETCHED PRICE'].fillna(df.get('CURRENT PRICE', df['AVERAGE PRICE']))
    
    # 4. Add previous close for today's return calculation
    df['PREV CLOSE'] = df['SYMBOL'].map(prev_close_map)
    
    # Check for critical missing data after fetch
    if df['CURRENT PRICE'].isnull().any():
        st.warning("⚠️ Some current prices could not be fetched. Using Average Price for calculation.")
    
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

# Main app
def main() -> None:
    """Main application entry point."""
    # --- Sidebar Controls (Nirnay-style) ---
    with st.sidebar:
        st.markdown("""
        <div style="text-align: center; padding: 1rem 0; margin-bottom: 1rem;">
            <div style="font-size: 1.75rem; font-weight: 800; color: #FFC300;">SAMHITA</div>
            <div style="color: #888888; font-size: 0.75rem; margin-top: 0.25rem;">संहिता | Portfolio Tracker</div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">🔄 Data Controls</div>', unsafe_allow_html=True)
        
        # Clear cache button (forces fresh fetch on next load)
        if st.button("REFRESH PRICES", help="Clear cached prices and fetch fresh data"):
            st.cache_data.clear()
            st.toast("Price cache cleared!", icon="🔄")
            st.rerun()
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        st.markdown('<div class="sidebar-title">📊 View Mode</div>', unsafe_allow_html=True)
        view_mode = st.radio(
            "Select View",
            ["📈 Dashboard", "📉 Analysis Mode"],
            label_visibility="collapsed"
        )
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        # Anchor Date for Analysis Mode
        st.markdown('<div class="sidebar-title">📅 Anchor Date</div>', unsafe_allow_html=True)
        st.caption("Set a custom start date for Analysis Mode metrics")
        
        use_anchor = st.toggle("Enable Anchor Date", value=False, key="use_anchor_date")
        
        anchor_date = None
        if use_anchor:
            anchor_date = st.date_input(
                "Investment Start Date",
                value=datetime.now() - timedelta(days=365),
                max_value=datetime.now().date(),
                min_value=datetime(2010, 1, 1).date(),
                label_visibility="collapsed"
            )
            st.caption(f"📌 Metrics calculated from {anchor_date.strftime('%b %d, %Y')}")
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        
        st.markdown(f"""
        <div class='info-box'>
            <p style='font-size: 0.8rem; margin: 0; color: var(--text-muted); line-height: 1.5;'>
                <strong>Version:</strong> {VERSION}<br>
                <strong>Data:</strong> Yahoo Finance<br>
                <strong>Refresh:</strong> Every 5 minutes
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    # Header - Using the premium-header structure
    st.markdown(f"""
        <div class="premium-header">
            <h1>SAMHITA : Portfolio Tracker</h1>
            <div class="tagline">Real-Time ETF Analytics & Performance Insights</div>
        </div>
    """, unsafe_allow_html=True)

    # Load data
    df = load_data()
    if df is None:
        return

    # Verify required columns
    required_columns = ['ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE']
    if not all(col in df.columns for col in required_columns):
        st.error(f"Excel file must contain: {', '.join(required_columns)}. The 'CURRENT PRICE' column is now automatically fetched.")
        return

    # Calculate metrics
    df, metrics = calculate_metrics(df)

    # Portfolio Snapshot Section
    st.markdown("""
        <div class='section'>
            <div class='section-header'>
                <h3 class='section-title'>Portfolio Snapshot</h3>
                <p class='section-subtitle'>Overview of your investment performance (Prices are near real-time)</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Metrics in 4 columns (Holdings moved to dedicated tab)
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class='metric-card primary'>
                <h4>Total Portfolio Value</h4>
                <h2 style='color: var(--primary-color);'>{format_currency(metrics['Total Current Value'])}</h2>
                <div class='sub-metric'>Invested: {format_currency(metrics['Total Invested'])}</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        gain_val = metrics['Total Gain']
        gain_class = 'success' if gain_val >= 0 else 'danger'
        gain_color = 'success-green' if gain_val >= 0 else 'danger-red'
        gain_sign = '+' if gain_val > 0 else ''
        st.markdown(f"""
            <div class='metric-card {gain_class}'>
                <h4>Absolute Gain/Loss</h4>
                <h2 style='color: var(--{gain_color});'>
                    {gain_sign}{format_currency(gain_val)}
                </h2>
                <div class='sub-metric'>Since inception</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        return_val = metrics['Portfolio Return %']
        return_class = 'success' if return_val >= 0 else 'danger'
        return_color = 'success-green' if return_val >= 0 else 'danger-red'
        return_sign = '+' if return_val > 0 else ''
        st.markdown(f"""
            <div class='metric-card {return_class}'>
                <h4>Total Return</h4>
                <h2 style='color: var(--{return_color});'>
                    {return_sign}{return_val:.2f}%
                </h2>
                <div class='sub-metric'>Portfolio XIRR equivalent</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        today_val = metrics['Today Return %']
        today_change = metrics['Today Change']
        today_class = 'success' if today_val >= 0 else 'danger'
        today_color = 'success-green' if today_val >= 0 else 'danger-red'
        today_sign = '+' if today_val > 0 else ''
        change_sign = '+' if today_change > 0 else ''
        st.markdown(f"""
            <div class='metric-card {today_class}'>
                <h4>Today's Return</h4>
                <h2 style='color: var(--{today_color});'>
                    {today_sign}{today_val:.2f}%
                </h2>
                <div class='sub-metric'>{change_sign}{format_currency(today_change)}</div>
            </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # DASHBOARD VIEW (Default)
    # =========================================================================
    if view_mode == "📈 Dashboard":
        # Tabs for detailed views
        tab1, tab2, tab3 = st.tabs(["**📊 Performance Analysis**", "**📋 Portfolio Details**", "**🎯 Holdings Analytics**"])

        with tab1:
            # =========================================================================
            # PERFORMANCE SNAPSHOT - Quick Summary Metrics
            # =========================================================================
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Performance Snapshot</h3>
                        <p class='section-subtitle'>Current portfolio performance summary (cost basis returns)</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Calculate snapshot metrics
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
            
            # Row 1: Key metrics
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            with c1:
                cls = 'success' if total_gain >= 0 else 'danger'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Total P&L</h4>
                        <h2>{format_currency(total_gain)}</h2>
                        <div class='sub-metric'>{total_return_pct:+.2f}% return</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                win_rate = (n_winners / n_total * 100) if n_total > 0 else 0
                cls = 'success' if win_rate > 50 else 'warning' if win_rate > 30 else 'danger'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Win Rate</h4>
                        <h2>{win_rate:.0f}%</h2>
                        <div class='sub-metric'>{n_winners}W / {n_losers}L</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c3:
                avg_winner_cls = 'success' if avg_winner > 0 else 'neutral' if n_winners == 0 else 'warning'
                st.markdown(f"""
                    <div class='metric-card {avg_winner_cls}'>
                        <h4>Avg Winner</h4>
                        <h2>{avg_winner:+.1f}%</h2>
                        <div class='sub-metric'>{n_winners} positions</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c4:
                avg_loser_cls = 'danger' if avg_loser < 0 else 'neutral' if n_losers == 0 else 'warning'
                st.markdown(f"""
                    <div class='metric-card {avg_loser_cls}'>
                        <h4>Avg Loser</h4>
                        <h2>{avg_loser:.1f}%</h2>
                        <div class='sub-metric'>{n_losers} positions</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c5:
                best_cls = 'success' if best_performer['GAIN %'] > 0 else 'danger' if best_performer['GAIN %'] < 0 else 'neutral'
                st.markdown(f"""
                    <div class='metric-card {best_cls}'>
                        <h4>Best Performer</h4>
                        <h2>{best_performer['GAIN %']:+.1f}%</h2>
                        <div class='sub-metric'>{best_performer['SYMBOL']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c6:
                worst_cls = 'danger' if worst_performer['GAIN %'] < 0 else 'success' if worst_performer['GAIN %'] > 0 else 'neutral'
                st.markdown(f"""
                    <div class='metric-card {worst_cls}'>
                        <h4>Worst Performer</h4>
                        <h2>{worst_performer['GAIN %']:.1f}%</h2>
                        <div class='sub-metric'>{worst_performer['SYMBOL']}</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # =========================================================================
            # TOP MOVERS - Side by side gainers and losers
            # =========================================================================
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Top Movers</h3>
                        <p class='section-subtitle'>Highest impact positions by absolute return and portfolio contribution</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col_gainers, col_losers = st.columns(2)
            
            with col_gainers:
                st.markdown("#### 🟢 Top Gainers")
                top_5_gainers = df.nlargest(5, 'GAIN %')[['SYMBOL', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'GAIN']]
                
                fig_gainers = go.Figure()
                fig_gainers.add_trace(go.Bar(
                    y=top_5_gainers['SYMBOL'][::-1],
                    x=top_5_gainers['GAIN %'][::-1],
                    orientation='h',
                    marker_color='#10b981',
                    text=[f"{x:+.1f}%" for x in top_5_gainers['GAIN %'][::-1]],
                    textposition='outside',
                    textfont=dict(size=11),
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Weight: %{customdata[0]:.1f}%<br>Contribution: %{customdata[1]:.2f}%<extra></extra>",
                    customdata=top_5_gainers[['WT', 'WEIGHTED RETURN %']][::-1].values
                ))
                fig_gainers.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#EAEAEA"),
                    margin=dict(l=10, r=60, t=50, b=40),
                    title=dict(text="Absolute Return %", font=dict(size=11, color='#888888'), x=0, xanchor='left'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=''),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    height=250,
                    showlegend=False
                )
                st.plotly_chart(fig_gainers, width="stretch")
            
            with col_losers:
                st.markdown("#### 🔴 Top Losers")
                top_5_losers = df.nsmallest(5, 'GAIN %')[['SYMBOL', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'GAIN']]
                
                fig_losers = go.Figure()
                fig_losers.add_trace(go.Bar(
                    y=top_5_losers['SYMBOL'],
                    x=top_5_losers['GAIN %'],
                    orientation='h',
                    marker_color='#ef4444',
                    text=[f"{x:.1f}%" for x in top_5_losers['GAIN %']],
                    textposition='outside',
                    textfont=dict(size=11),
                    hovertemplate="<b>%{y}</b><br>Return: %{x:.2f}%<br>Weight: %{customdata[0]:.1f}%<br>Contribution: %{customdata[1]:.2f}%<extra></extra>",
                    customdata=top_5_losers[['WT', 'WEIGHTED RETURN %']].values
                ))
                fig_losers.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#EAEAEA"),
                    margin=dict(l=10, r=60, t=50, b=40),
                    title=dict(text="Absolute Return %", font=dict(size=11, color='#888888'), x=0, xanchor='left'),
                    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=''),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    height=250,
                    showlegend=False
                )
                st.plotly_chart(fig_losers, width="stretch")
            
            # =========================================================================
            # PERFORMANCE SCATTER - Return vs Weight
            # =========================================================================
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Risk-Return Profile</h3>
                        <p class='section-subtitle'>Position performance vs portfolio weight (bubble size = current value)</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Normalize bubble sizes
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
                    colorscale=[[0, '#ef4444'], [0.5, '#FFC300'], [1, '#10b981']],
                    cmid=0,
                    line=dict(width=1, color='#EAEAEA'),
                    opacity=0.8
                ),
                text=df['SYMBOL'],
                textposition='top center',
                textfont=dict(size=9, color='#EAEAEA'),
                hovertemplate="<b>%{text}</b><br>Weight: %{x:.1f}%<br>Return: %{y:.2f}%<br>Value: ₹%{customdata:,.0f}<extra></extra>",
                customdata=df['CURR. VALUE']
            ))
            
            # Add quadrant lines
            fig_scatter.add_hline(y=0, line_dash="dash", line_color="#888888", line_width=1)
            avg_weight = df['WT'].mean()
            fig_scatter.add_vline(x=avg_weight, line_dash="dash", line_color="#888888", line_width=1,
                                 annotation_text=f"Avg Wt: {avg_weight:.1f}%", annotation_position="top")
            
            fig_scatter.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#EAEAEA"),
                margin=dict(l=10, r=10, t=50, b=50),
                title=dict(text="Weight vs Return Matrix", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
                xaxis=dict(title='Portfolio Weight (%)', gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Gain/Loss (%)', gridcolor='rgba(255,255,255,0.05)'),
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_scatter, width='stretch')
            
            # =========================================================================
            # CONTRIBUTION WATERFALL
            # =========================================================================
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Return Attribution</h3>
                        <p class='section-subtitle'>Contribution of each holding to total portfolio return</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Sort by contribution
            contrib_sorted = df.sort_values('WEIGHTED RETURN %', ascending=False).copy()
            
            fig_waterfall = go.Figure()
            
            colors = ['#10b981' if x >= 0 else '#ef4444' for x in contrib_sorted['WEIGHTED RETURN %']]
            
            fig_waterfall.add_trace(go.Bar(
                x=contrib_sorted['SYMBOL'],
                y=contrib_sorted['WEIGHTED RETURN %'],
                marker_color=colors,
                text=[f"{x:+.2f}%" for x in contrib_sorted['WEIGHTED RETURN %']],
                textposition='outside',
                textfont=dict(size=10, color='#EAEAEA'),
                hovertemplate="<b>%{x}</b><br>Contribution: %{y:.3f}%<br>Return: %{customdata[0]:.1f}%<br>Weight: %{customdata[1]:.1f}%<extra></extra>",
                customdata=contrib_sorted[['GAIN %', 'WT']].values
            ))
            
            fig_waterfall.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#EAEAEA"),
                margin=dict(l=10, r=10, t=50, b=60),
                title=dict(text="Weighted Return Contribution (Sorted by Impact)", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
                xaxis=dict(tickangle=45, gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(title='Contribution (%)', gridcolor='rgba(255,255,255,0.05)'),
                height=400,
                showlegend=False
            )
            st.plotly_chart(fig_waterfall, width='stretch')
            
            # =========================================================================
            # PORTFOLIO COMPOSITION TREEMAP
            # =========================================================================
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Portfolio Composition</h3>
                        <p class='section-subtitle'>Asset allocation by current value</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Dynamic color scale logic
            min_gain_pct = df['GAIN %'].min()
            max_gain_pct = df['GAIN %'].max()
            
            color_scale_config = {}
            
            if min_gain_pct >= 0:
                color_scale_config['color_continuous_scale'] = ['#FFC300', '#10b981']
                color_scale_config['range_color'] = [min_gain_pct, max_gain_pct]
            elif max_gain_pct <= 0:
                color_scale_config['color_continuous_scale'] = ['#f87171', '#ef4444']
                color_scale_config['range_color'] = [min_gain_pct, max_gain_pct]
            else:
                color_scale_config['color_continuous_scale'] = ['#ef4444', '#FFC300', '#10b981']
                color_scale_config['color_continuous_midpoint'] = 0
            
            fig_treemap = px.treemap(
                df,
                path=['SYMBOL'],
                values='CURR. VALUE',
                color='GAIN %',
                **color_scale_config 
            )
            fig_treemap.update_layout(
                margin=dict(t=50, l=10, r=10, b=10),
                paper_bgcolor='rgba(0,0,0,0)',
                font_color='#EAEAEA',
                title=dict(text="Value Allocation (Color = Gain/Loss %)", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
                height=400
            )
            st.plotly_chart(fig_treemap, width='stretch')

        with tab2:
            # Portfolio Holdings Table
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Portfolio Holdings</h3>
                        <p class='section-subtitle'>Detailed view of all investments (Current Price is near real-time)</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            display_df = df[['ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE', 'INVESTED', 
                             'CURRENT PRICE', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT']].copy()
            
            # Add rank column
            display_df['RANK'] = display_df['CURR. VALUE'].rank(ascending=False).astype(int)
            display_df = display_df.sort_values('RANK')
            
            # Format columns
            display_df['AVERAGE PRICE'] = display_df['AVERAGE PRICE'].apply(format_currency)
            display_df['INVESTED'] = display_df['INVESTED'].apply(format_currency)
            display_df['CURRENT PRICE'] = display_df['CURRENT PRICE'].apply(format_currency)
            
            def format_gain(x):
                color = 'var(--success-green)' if x >= 0 else 'var(--danger-red)'
                return f"<span style='color: {color}'>{format_currency(x)}</span>"
            
            def format_gain_pct(x):
                color = 'var(--success-green)' if x >= 0 else 'var(--danger-red)'
                return f"<span style='color: {color}'>{x:.2f}%</span>"

            display_df['CURR. VALUE'] = display_df['CURR. VALUE'].apply(format_currency)
            display_df['GAIN'] = display_df['GAIN'].apply(format_gain)
            display_df['GAIN %'] = display_df['GAIN %'].apply(format_gain_pct)
            display_df['WT'] = display_df['WT'].apply(lambda x: f"{x:.2f}%")
            
            display_cols = ['RANK', 'ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE', 'CURRENT PRICE', 
                           'INVESTED', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT']
            display_df = display_df[display_cols]
            
            st.markdown(f"""
                <div class='table-container'>
                    <table class='table'>
                        {display_df.to_html(escape=False, index=False, classes='table')}
                    </table>
                </div>
            """, unsafe_allow_html=True)
            
            # Export button
            excel_data = to_excel(df)
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            st.download_button(
                "Export Raw Portfolio Data (Excel)",
                excel_data,
                file_name=f"Samhita_portfolio_details_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheet.sheet"
            )
        
        with tab3:
            # Holdings Analytics Tab - Institutional Grade
            st.markdown("""
                <div class='section'>
                    <div class='section-header'>
                        <h3 class='section-title'>Holdings Analytics</h3>
                        <p class='section-subtitle'>Institutional-grade concentration, diversification & risk decomposition</p>
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            # Calculate advanced metrics
            n_holdings = len(df)
            weights = df['WT'].values / 100  # Convert to decimal
            returns = df['GAIN %'].values / 100
            
            # Concentration metrics
            hhi = (df['WT'] ** 2).sum()
            effective_n = 10000 / hhi if hhi > 0 else n_holdings
            gini = 0
            if n_holdings > 1:
                sorted_weights = np.sort(weights)
                cum_weights = np.cumsum(sorted_weights)
                gini = 1 - 2 * np.sum(cum_weights) / (n_holdings * cum_weights[-1]) if cum_weights[-1] > 0 else 0
            
            # Diversification ratio (simplified)
            avg_weight = weights.mean()
            weight_std = weights.std()
            div_ratio = 1 / (hhi / 10000) if hhi > 0 else n_holdings
            
            # Row 1: Concentration Metrics
            st.markdown("#### Concentration Metrics")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            with c1:
                st.markdown(f"""
                    <div class='metric-card primary'>
                        <h4>Holdings</h4>
                        <h2>{n_holdings}</h2>
                        <div class='sub-metric'>Unique positions</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                top5 = metrics['Top 5 Concentration']
                cls = 'warning' if top5 > 60 else 'success'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Top 5</h4>
                        <h2>{top5:.1f}%</h2>
                        <div class='sub-metric'>Concentration</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c3:
                top10 = df['WT'].nlargest(10).sum()
                cls = 'warning' if top10 > 80 else 'success'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Top 10</h4>
                        <h2>{top10:.1f}%</h2>
                        <div class='sub-metric'>Concentration</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c4:
                st.markdown(f"""
                    <div class='metric-card info'>
                        <h4>Effective N</h4>
                        <h2>{effective_n:.1f}</h2>
                        <div class='sub-metric'>1/HHI equivalent</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c5:
                cls = 'warning' if hhi > 1500 else 'success'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>HHI</h4>
                        <h2>{hhi:.0f}</h2>
                        <div class='sub-metric'><1500 = diverse</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c6:
                st.markdown(f"""
                    <div class='metric-card neutral'>
                        <h4>Gini Coeff</h4>
                        <h2>{gini:.2f}</h2>
                        <div class='sub-metric'>0=equal, 1=conc</div>
                    </div>
                """, unsafe_allow_html=True)
            
            # Row 2: Performance Distribution
            st.markdown("#### Performance Distribution")
            c1, c2, c3, c4, c5, c6 = st.columns(6)
            
            profitable = (df['GAIN %'] > 0).sum()
            losing = (df['GAIN %'] < 0).sum()
            breakeven = n_holdings - profitable - losing
            win_rate = profitable / n_holdings * 100 if n_holdings > 0 else 0
            
            with c1:
                st.markdown(f"""
                    <div class='metric-card success'>
                        <h4>Winners</h4>
                        <h2>{profitable}</h2>
                        <div class='sub-metric'>Profitable</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c2:
                st.markdown(f"""
                    <div class='metric-card danger'>
                        <h4>Losers</h4>
                        <h2>{losing}</h2>
                        <div class='sub-metric'>Underwater</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c3:
                cls = 'success' if win_rate > 60 else 'warning' if win_rate > 40 else 'danger'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Win Rate</h4>
                        <h2>{win_rate:.0f}%</h2>
                        <div class='sub-metric'>Batting avg</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c4:
                avg_gain = df['GAIN %'].mean()
                cls = 'success' if avg_gain > 0 else 'danger'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Avg Return</h4>
                        <h2>{avg_gain:+.1f}%</h2>
                        <div class='sub-metric'>Mean gain</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c5:
                median_gain = df['GAIN %'].median()
                cls = 'success' if median_gain > 0 else 'danger'
                st.markdown(f"""
                    <div class='metric-card {cls}'>
                        <h4>Median Return</h4>
                        <h2>{median_gain:+.1f}%</h2>
                        <div class='sub-metric'>50th percentile</div>
                    </div>
                """, unsafe_allow_html=True)
            
            with c6:
                gain_std = df['GAIN %'].std()
                st.markdown(f"""
                    <div class='metric-card warning'>
                        <h4>Return Dispersion</h4>
                        <h2>{gain_std:.1f}%</h2>
                        <div class='sub-metric'>Std deviation</div>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # Charts Row
            col_pie, col_lorenz = st.columns(2)
            
            with col_pie:
                st.markdown("#### Weight Distribution")
                
                # Treemap for weight distribution
                fig_tree = px.treemap(
                    df,
                    path=['SYMBOL'],
                    values='WT',
                    color='GAIN %',
                    color_continuous_scale=['#ef4444', '#FFC300', '#10b981'],
                    color_continuous_midpoint=0
                )
                fig_tree.update_layout(
                    margin=dict(t=50, l=10, r=10, b=10),
                    paper_bgcolor='rgba(0,0,0,0)',
                    font_color='#EAEAEA',
                    title=dict(text="Weight % (Color = Gain/Loss)", font=dict(size=11, color='#888888'), x=0, xanchor='left'),
                    height=340
                )
                fig_tree.update_coloraxes(showscale=False)
                st.plotly_chart(fig_tree, width="stretch")
            
            with col_lorenz:
                st.markdown("#### Concentration Curve")
                
                # Lorenz curve
                sorted_weights = np.sort(df['WT'].values)[::-1]
                cum_weights = np.cumsum(sorted_weights)
                n = len(sorted_weights)
                
                fig_lorenz = go.Figure()
                
                # Perfect equality line
                fig_lorenz.add_trace(go.Scatter(
                    x=list(range(n + 1)),
                    y=[0] + list(np.linspace(0, 100, n)),
                    mode='lines',
                    name='Equal Weight',
                    line=dict(color='#888888', dash='dash', width=1)
                ))
                
                # Actual concentration curve
                fig_lorenz.add_trace(go.Scatter(
                    x=list(range(n + 1)),
                    y=[0] + list(cum_weights),
                    mode='lines+markers',
                    name='Portfolio',
                    line=dict(color='#FFC300', width=2),
                    marker=dict(size=4),
                    fill='tonexty',
                    fillcolor='rgba(255, 195, 0, 0.15)'
                ))
                
                # Key thresholds
                fig_lorenz.add_hline(y=50, line_dash="dot", line_color="#10b981", 
                                    annotation_text="50%", annotation_position="right")
                fig_lorenz.add_hline(y=80, line_dash="dot", line_color="#06b6d4",
                                    annotation_text="80%", annotation_position="right")
                
                fig_lorenz.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#EAEAEA"),
                    margin=dict(l=10, r=10, t=50, b=45),
                    title=dict(text="Lorenz Curve (Cumulative %)", font=dict(size=11, color='#888888'), x=0, xanchor='left'),
                    xaxis=dict(title='# Holdings (ranked)', gridcolor='rgba(255,255,255,0.05)'),
                    yaxis=dict(title='Cumulative Weight (%)', gridcolor='rgba(255,255,255,0.05)', range=[0, 105]),
                    height=340,
                    showlegend=True,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_lorenz, width="stretch")
            
            st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
            
            # Risk Contribution Table
            st.markdown("#### Risk & Return Contribution")
            
            # Calculate contribution metrics
            contrib_df = df[['SYMBOL', 'ASSET NAME', 'WT', 'GAIN %', 'WEIGHTED RETURN %']].copy()
            contrib_df['Weight'] = contrib_df['WT'].apply(lambda x: f"{x:.2f}%")
            contrib_df['Return'] = contrib_df['GAIN %'].apply(lambda x: f"{x:+.2f}%")
            contrib_df['Contribution'] = contrib_df['WEIGHTED RETURN %'].apply(lambda x: f"{x:+.3f}%")
            
            # Risk contribution (simplified - weight^2 as proxy)
            contrib_df['Risk Weight'] = (contrib_df['WT'] ** 2) / hhi * 100
            contrib_df['Risk Contrib'] = contrib_df['Risk Weight'].apply(lambda x: f"{x:.1f}%")
            
            # Sort by contribution
            contrib_df = contrib_df.sort_values('WEIGHTED RETURN %', ascending=False)
            
            # Create horizontal bar chart
            fig_contrib = make_subplots(rows=1, cols=2, shared_yaxes=True,
                                       subplot_titles=('Return Contribution', 'Risk Contribution'),
                                       horizontal_spacing=0.02)
            
            colors_ret = ['#10b981' if x >= 0 else '#ef4444' for x in contrib_df['WEIGHTED RETURN %']]
            
            fig_contrib.add_trace(go.Bar(
                y=contrib_df['SYMBOL'],
                x=contrib_df['WEIGHTED RETURN %'],
                orientation='h',
                marker_color=colors_ret,
                text=[f"{x:.2f}%" for x in contrib_df['WEIGHTED RETURN %']],
                textposition='outside',
                textfont=dict(size=9),
                showlegend=False
            ), row=1, col=1)
            
            fig_contrib.add_trace(go.Bar(
                y=contrib_df['SYMBOL'],
                x=contrib_df['Risk Weight'],
                orientation='h',
                marker_color='#FFC300',
                text=[f"{x:.1f}%" for x in contrib_df['Risk Weight']],
                textposition='outside',
                textfont=dict(size=9),
                showlegend=False
            ), row=1, col=2)
            
            fig_contrib.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#EAEAEA", size=10),
                margin=dict(l=10, r=60, t=50, b=40),
                height=max(350, n_holdings * 22 + 80),
                showlegend=False
            )
            
            fig_contrib.update_xaxes(gridcolor='rgba(255,255,255,0.05)')
            fig_contrib.update_yaxes(gridcolor='rgba(255,255,255,0.05)')
            
            st.plotly_chart(fig_contrib, width="stretch")
            
            # Summary Statistics in expander
            with st.expander("📊 Detailed Statistics", expanded=False):
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
    if view_mode == "📉 Analysis Mode":
        render_analysis_mode(df, metrics, anchor_date)
    
    # =========================================================================
    # FOOTER
    # =========================================================================
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now + timedelta(hours=5, minutes=30)
    current_time_ist = ist_now.strftime("%Y-%m-%d %H:%M:%S IST")
    st.caption(f"© 2026 {PRODUCT_NAME} | {COMPANY} | {VERSION} | {current_time_ist}")


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

@st.cache_data(ttl=300)
def fetch_analysis_data(
    symbols: list[str], days_back: int
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fetch historical data for portfolio and NIFTY 50 benchmark.
    Portfolio data is aligned to NIFTY 50 trading dates to avoid
    holiday/timezone edge cases.
    """
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    
    try:
        # First fetch NIFTY 50 to get valid trading dates
        benchmark_data = yf.download(
            tickers=BENCHMARK_TICKER,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d',
            progress=False
        )
        
        if benchmark_data.empty:
            return pd.DataFrame(), pd.DataFrame()
        
        # Get NIFTY 50 close prices
        benchmark_close = benchmark_data['Close']
        if isinstance(benchmark_close, pd.DataFrame):
            benchmark_close = benchmark_close.iloc[:, 0]
        benchmark_df = benchmark_close.to_frame(name=BENCHMARK_NAME)
        
        # Get valid trading dates from NIFTY 50
        valid_dates = benchmark_df.index
        
        # Now fetch portfolio holdings
        tickers = [f"{s}.NS" for s in symbols]
        
        portfolio_data = yf.download(
            tickers=tickers,
            start=start_date.strftime('%Y-%m-%d'),
            end=end_date.strftime('%Y-%m-%d'),
            interval='1d',
            progress=False,
            threads=True
        )
        
        if portfolio_data.empty:
            return pd.DataFrame(), benchmark_df
        
        # Get close prices
        if len(tickers) == 1:
            portfolio_close = portfolio_data['Close'].to_frame()
            portfolio_close.columns = [symbols[0]]
        else:
            portfolio_close = portfolio_data['Close']
            portfolio_close.columns = [c.replace('.NS', '') for c in portfolio_close.columns]
        
        # Align portfolio data to NIFTY 50 dates only
        portfolio_aligned = portfolio_close.reindex(valid_dates)
        
        # Forward fill any missing values (in case some stocks didn't trade)
        portfolio_aligned = portfolio_aligned.ffill()
        
        return portfolio_aligned, benchmark_df
        
    except Exception as e:
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
    """Render Bloomberg Terminal style analytics."""
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # =========================================================================
    # HEADER & TIMEFRAME SELECTOR
    # =========================================================================
    
    # Show anchor date info if active
    anchor_info = ""
    if anchor_date:
        anchor_info = f'<span style="color: #06b6d4; font-size: 0.8rem; margin-left: 1rem;">📌 Anchor: {anchor_date.strftime("%b %d, %Y")}</span>'
    
    st.markdown(f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem;">
            <div>
                <h2 style="margin: 0; color: #FFC300;">Portfolio Analytics Terminal{anchor_info}</h2>
                <p style="margin: 0; color: #888888; font-size: 0.9rem;">Institutional-Grade Performance Analysis</p>
            </div>
        </div>
    """, unsafe_allow_html=True)
    
    # Initialize session state
    if 'tf_selected' not in st.session_state:
        st.session_state.tf_selected = '1Y'
    
    # Timeframe buttons row (disabled when anchor date is active)
    if anchor_date:
        # Show toast notification
        st.toast(f"📅 Anchor Date Active: Metrics from {anchor_date.strftime('%b %d, %Y')}", icon="📌")
        # Calculate days from anchor date to today
        days_back = (datetime.now().date() - anchor_date).days + 1
        selected_tf = "CUSTOM"
        
        # Still show timeframe buttons but disabled style
        tf_cols = st.columns(len(TIMEFRAMES))
        for i, tf in enumerate(TIMEFRAMES.keys()):
            with tf_cols[i]:
                st.button(tf, key=f"tf_{tf}_disabled", use_container_width=True, disabled=True)
    else:
        tf_cols = st.columns(len(TIMEFRAMES))
        for i, tf in enumerate(TIMEFRAMES.keys()):
            with tf_cols[i]:
                btn_type = "primary" if st.session_state.tf_selected == tf else "secondary"
                if st.button(tf, key=f"tf_{tf}", use_container_width=True, type=btn_type):
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
    
    spinner_text = f"Loading data from {anchor_date.strftime('%b %d, %Y')}..." if anchor_date else f"Loading {selected_tf} data..."
    with st.spinner(spinner_text):
        portfolio_prices, benchmark_prices = fetch_analysis_data(symbols, days_back)
    
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
    port_returns = port_value.pct_change().dropna()
    
    # Get benchmark returns
    bench_returns = None
    if not benchmark_prices.empty and BENCHMARK_NAME in benchmark_prices.columns:
        bench_returns = benchmark_prices[BENCHMARK_NAME].pct_change().dropna()
    
    # Compute metrics
    m = compute_metrics(port_returns, bench_returns)
    
    # =========================================================================
    # MAIN COMPARISON CHART
    # =========================================================================
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    # Normalize to 100
    port_norm = (port_value / port_value.iloc[0]) * 100
    
    fig = go.Figure()
    
    # Portfolio trace
    port_ret_display = m.get('total_return', 0)
    fig.add_trace(go.Scatter(
        x=port_norm.index,
        y=port_norm.values,
        mode='lines',
        name=f'Portfolio ({port_ret_display:+.2f}%)',
        line=dict(color='#FFC300', width=2.5),
        hovertemplate='%{x|%b %d, %Y}<br>Portfolio: %{y:.2f}<extra></extra>'
    ))
    
    # Benchmark trace (NIFTY 50 only)
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
                line=dict(color='#06b6d4', width=2, dash='dot'),
                hovertemplate=f'%{{x|%b %d, %Y}}<br>{BENCHMARK_NAME}: %{{y:.2f}}<extra></extra>'
            ))
    
    # Layout
    fig.update_layout(
        template='plotly_dark',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color="#EAEAEA", size=12),
        margin=dict(l=10, r=10, t=10, b=10),
        xaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            showgrid=True,
            showspikes=False
        ),
        yaxis=dict(
            gridcolor='rgba(255,255,255,0.05)',
            showgrid=True,
            title='',
            side='right',
            showspikes=False
        ),
        height=420,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="center",
            x=0.5,
            bgcolor='rgba(0,0,0,0)',
            font=dict(size=11)
        ),
        hovermode='closest'
    )
    
    # Range selector settings
    fig.update_xaxes(
        rangeslider=dict(visible=False),
        rangeselector=dict(visible=False)
    )
    
    st.plotly_chart(fig, width="stretch", config={
        'displayModeBar': True,
        'displaylogo': False,
        'modeBarButtonsToRemove': ['lasso2d', 'select2d']
    })
    
    # =========================================================================
    # PERFORMANCE SUMMARY - ROW 1 (Returns & Risk-Adjusted)
    # =========================================================================
    
    st.markdown("#### Returns & Risk-Adjusted Performance")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        val = m.get('total_return', 0)
        cls = 'success' if val >= 0 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Period Return</h4>
                <h2>{val:+.2f}%</h2>
                <div class='sub-metric'>CAGR: {m.get('cagr', 0):+.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        alpha = m.get('alpha', 0)
        cls = 'success' if alpha > 0 else 'danger' if alpha < 0 else 'neutral'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Alpha</h4>
                <h2>{alpha:+.2f}%</h2>
                <div class='sub-metric'>Excess return</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c3:
        sharpe = m.get('sharpe', 0)
        cls = 'success' if sharpe > 1 else 'warning' if sharpe > 0.5 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Sharpe</h4>
                <h2>{sharpe:.2f}</h2>
                <div class='sub-metric'>Rf = 6.5%</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c4:
        sortino = m.get('sortino', 0)
        cls = 'success' if sortino > 1.5 else 'warning' if sortino > 0.5 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Sortino</h4>
                <h2>{sortino:.2f}</h2>
                <div class='sub-metric'>Downside risk</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c5:
        calmar = m.get('calmar', 0)
        cls = 'success' if calmar > 1 else 'warning' if calmar > 0.5 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Calmar</h4>
                <h2>{calmar:.2f}</h2>
                <div class='sub-metric'>Return/MaxDD</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c6:
        ir = m.get('info_ratio', 0)
        cls = 'success' if ir > 0.5 else 'warning' if ir > 0 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Info Ratio</h4>
                <h2>{ir:.2f}</h2>
                <div class='sub-metric'>Active return/TE</div>
            </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # ROW 2 - RISK METRICS
    # =========================================================================
    
    st.markdown("#### Risk Metrics")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        vol = m.get('volatility', 0)
        st.markdown(f"""
            <div class='metric-card warning'>
                <h4>Volatility</h4>
                <h2>{vol:.1f}%</h2>
                <div class='sub-metric'>Annualized</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        mdd = m.get('max_drawdown', 0)
        cls = 'danger' if mdd < -20 else 'warning' if mdd < -10 else 'success'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Max Drawdown</h4>
                <h2>{mdd:.1f}%</h2>
                <div class='sub-metric'>Peak to trough</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c3:
        var95 = m.get('var_95', 0)
        st.markdown(f"""
            <div class='metric-card danger'>
                <h4>VaR (95%)</h4>
                <h2>{var95:.2f}%</h2>
                <div class='sub-metric'>Daily at risk</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c4:
        cvar = m.get('cvar_95', 0)
        st.markdown(f"""
            <div class='metric-card danger'>
                <h4>CVaR (95%)</h4>
                <h2>{cvar:.2f}%</h2>
                <div class='sub-metric'>Expected shortfall</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c5:
        beta = m.get('beta', 1)
        cls = 'warning' if beta > 1.2 else 'info' if beta < 0.8 else 'neutral'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Beta</h4>
                <h2>{beta:.2f}</h2>
                <div class='sub-metric'>Market sensitivity</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c6:
        te = m.get('tracking_error', 0)
        st.markdown(f"""
            <div class='metric-card info'>
                <h4>Tracking Error</h4>
                <h2>{te:.1f}%</h2>
                <div class='sub-metric'>vs Benchmark</div>
            </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # ROW 3 - BENCHMARK COMPARISON
    # =========================================================================
    
    st.markdown("#### Benchmark Comparison")
    
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    
    with c1:
        bench_ret = m.get('benchmark_return', 0)
        cls = 'success' if bench_ret >= 0 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Benchmark</h4>
                <h2>{bench_ret:+.1f}%</h2>
                <div class='sub-metric'>{BENCHMARK_NAME}</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c2:
        excess = m.get('total_return', 0) - m.get('benchmark_return', 0)
        cls = 'success' if excess > 0 else 'danger'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Excess Return</h4>
                <h2>{excess:+.1f}%</h2>
                <div class='sub-metric'>vs Benchmark</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c3:
        up_cap = m.get('up_capture', 100)
        cls = 'success' if up_cap > 100 else 'warning'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Up Capture</h4>
                <h2>{up_cap:.0f}%</h2>
                <div class='sub-metric'>Bull market</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c4:
        down_cap = m.get('down_capture', 100)
        cls = 'success' if down_cap < 100 else 'warning'
        st.markdown(f"""
            <div class='metric-card {cls}'>
                <h4>Down Capture</h4>
                <h2>{down_cap:.0f}%</h2>
                <div class='sub-metric'>Bear market</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c5:
        r2 = m.get('r_squared', 0)
        st.markdown(f"""
            <div class='metric-card info'>
                <h4>R-Squared</h4>
                <h2>{r2:.2f}</h2>
                <div class='sub-metric'>Explained variance</div>
            </div>
        """, unsafe_allow_html=True)
    
    with c6:
        corr = m.get('correlation', 0)
        st.markdown(f"""
            <div class='metric-card info'>
                <h4>Correlation</h4>
                <h2>{corr:.2f}</h2>
                <div class='sub-metric'>vs Benchmark</div>
            </div>
        """, unsafe_allow_html=True)
    
    # =========================================================================
    # DRAWDOWN & DISTRIBUTION CHARTS
    # =========================================================================
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    col_dd, col_dist = st.columns(2)
    
    with col_dd:
        st.markdown("#### Drawdown Analysis")
        
        dd_series = m.get('drawdown_series', pd.Series())
        if len(dd_series) > 0:
            fig_dd = go.Figure()
            fig_dd.add_trace(go.Scatter(
                x=dd_series.index,
                y=dd_series.values,
                mode='lines',
                fill='tozeroy',
                line=dict(color='#ef4444', width=1),
                fillcolor='rgba(239, 68, 68, 0.3)',
                hovertemplate='%{x|%b %d, %Y}<br>Drawdown: %{y:.2f}%<extra></extra>'
            ))
            
            fig_dd.add_hline(
                y=m.get('max_drawdown', 0),
                line_dash="dash",
                line_color="#FFC300",
                annotation_text=f"Max: {m.get('max_drawdown', 0):.1f}%",
                annotation_position="right"
            )
            
            fig_dd.update_layout(
                template='plotly_dark',
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                font=dict(color="#EAEAEA"),
                margin=dict(l=10, r=10, t=50, b=40),
                title=dict(text="Underwater Equity Curve", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
                xaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                yaxis=dict(gridcolor='rgba(255,255,255,0.05)', title=''),
                height=300,
                showlegend=False
            )
            st.plotly_chart(fig_dd, width="stretch")
    
    with col_dist:
        st.markdown("#### Returns Distribution")
        
        fig_hist = go.Figure()
        fig_hist.add_trace(go.Histogram(
            x=port_returns * 100,
            nbinsx=40,
            marker_color='#FFC300',
            opacity=0.75,
            hovertemplate='Return: %{x:.2f}%<br>Count: %{y}<extra></extra>'
        ))
        
        fig_hist.add_vline(x=0, line_dash="dash", line_color="#888888", line_width=1)
        fig_hist.add_vline(
            x=port_returns.mean() * 100,
            line_dash="dot",
            line_color="#10b981",
            annotation_text=f"μ: {port_returns.mean()*100:.2f}%",
            annotation_position="top"
        )
        fig_hist.add_vline(
            x=m.get('var_95', 0),
            line_dash="dash",
            line_color="#ef4444",
            annotation_text=f"VaR: {m.get('var_95', 0):.1f}%",
            annotation_position="bottom left"
        )
        
        fig_hist.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#EAEAEA"),
            margin=dict(l=10, r=10, t=50, b=40),
            title=dict(text="Daily Returns Histogram", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
            xaxis=dict(title='Daily Return (%)', gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title='', gridcolor='rgba(255,255,255,0.05)'),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig_hist, width="stretch")
    
    # =========================================================================
    # ROLLING METRICS
    # =========================================================================
    
    # =========================================================================
    # ROLLING ANALYTICS (Dynamic window based on timeframe)
    # =========================================================================
    
    # Calculate appropriate window based on data length
    data_length = len(port_returns)
    
    # Dynamic window: use 1/3 of data or cap at 63 days
    if data_length < 15:
        # Not enough data for rolling analytics
        pass
    else:
        rolling_window = min(63, max(10, data_length // 3))
        
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown(f"#### Rolling Analytics ({rolling_window}-day)")
        
        col_rs, col_rb = st.columns(2)
        
        with col_rs:
            # Rolling Sharpe
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
                    line=dict(color='#FFC300', width=1.5),
                    hovertemplate='%{x|%b %d, %Y}<br>Sharpe: %{y:.2f}<extra></extra>'
                ))
                fig_rs.add_hline(y=1, line_dash="dash", line_color="#10b981", annotation_text="Target", annotation_position="right")
                fig_rs.add_hline(y=0, line_dash="dash", line_color="#888888")
                
                fig_rs.update_layout(
                    template='plotly_dark',
                    plot_bgcolor='rgba(0,0,0,0)',
                    paper_bgcolor='rgba(0,0,0,0)',
                    font=dict(color="#EAEAEA"),
                    margin=dict(l=10, r=10, t=50, b=40),
                    title=dict(text="Rolling Sharpe Ratio", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
                    xaxis=dict(
                        gridcolor='rgba(255,255,255,0.05)',
                        tickformat='%b %Y'
                    ),
                    yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                    height=280,
                    showlegend=False
                )
                st.plotly_chart(fig_rs, width="stretch")
        
        with col_rb:
            # Rolling Beta
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
                            line=dict(color='#06b6d4', width=1.5),
                            hovertemplate='%{x|%b %d, %Y}<br>Beta: %{y:.2f}<extra></extra>'
                        ))
                        fig_rb.add_hline(y=1, line_dash="dash", line_color="#888888", annotation_text="Market", annotation_position="right")
                        
                        fig_rb.update_layout(
                            template='plotly_dark',
                            plot_bgcolor='rgba(0,0,0,0)',
                            paper_bgcolor='rgba(0,0,0,0)',
                            font=dict(color="#EAEAEA"),
                            margin=dict(l=10, r=10, t=50, b=40),
                            title=dict(text="Rolling Beta vs NIFTY 50", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
                            xaxis=dict(
                                gridcolor='rgba(255,255,255,0.05)',
                                tickformat='%b %Y'
                            ),
                            yaxis=dict(gridcolor='rgba(255,255,255,0.05)'),
                            height=280,
                            showlegend=False
                        )
                        st.plotly_chart(fig_rb, width="stretch")
    
    # =========================================================================
    # MONTHLY RETURNS HEATMAP
    # =========================================================================
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### Monthly Returns Heatmap")
    
    # Calculate monthly returns
    monthly = port_value.resample('ME').last().pct_change().dropna() * 100
    
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
        
        # Create heatmap
        fig_heat = go.Figure(data=go.Heatmap(
            z=heatmap_data,
            x=col_labels,
            y=year_labels,
            colorscale=[[0, '#ef4444'], [0.5, '#1A1A1A'], [1, '#10b981']],
            zmid=0,
            text=[[f"{v:.1f}%" if pd.notna(v) else "" for v in row] for row in heatmap_data],
            texttemplate="%{text}",
            textfont=dict(size=10, color="#EAEAEA"),
            hovertemplate="Year: %{y}<br>%{x}: %{z:.2f}%<extra></extra>",
            showscale=False
        ))
        
        fig_heat.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#EAEAEA"),
            margin=dict(l=10, r=10, t=70, b=20),
            title=dict(text="Month-over-Month Returns (%)", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
            xaxis=dict(side='top', tickangle=0, type='category', dtick=1),
            yaxis=dict(autorange='reversed', type='category', dtick=1),
            height=max(160, len(years) * 38 + 80)
        )
        
        st.plotly_chart(fig_heat, width="stretch")
    
    # =========================================================================
    # HOLDING ATTRIBUTION
    # =========================================================================
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### Holding Attribution")
    
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
                    'Contribution': contrib
                })
    
    if attribution:
        attr_df = pd.DataFrame(attribution).sort_values('Contribution', ascending=True)
        
        fig_attr = go.Figure()
        
        colors = ['#10b981' if x >= 0 else '#ef4444' for x in attr_df['Contribution']]
        
        fig_attr.add_trace(go.Bar(
            y=attr_df['Symbol'],
            x=attr_df['Contribution'],
            orientation='h',
            marker_color=colors,
            text=[f"{x:+.2f}%" for x in attr_df['Contribution']],
            textposition='outside',
            textfont=dict(size=10),
            hovertemplate="<b>%{y}</b><br>Return: %{customdata[0]:.1f}%<br>Weight: %{customdata[1]:.1f}%<br>Contribution: %{x:.2f}%<extra></extra>",
            customdata=attr_df[['Return', 'Weight']].values
        ))
        
        fig_attr.update_layout(
            template='plotly_dark',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#EAEAEA"),
            margin=dict(l=10, r=60, t=50, b=40),
            title=dict(text="Contribution to Portfolio Return (%)", font=dict(size=12, color='#888888'), x=0, xanchor='left'),
            xaxis=dict(title='', gridcolor='rgba(255,255,255,0.05)'),
            yaxis=dict(title='', gridcolor='rgba(255,255,255,0.05)'),
            height=max(320, len(attr_df) * 25 + 70),
            showlegend=False
        )
        
        st.plotly_chart(fig_attr, width="stretch")
    
    # =========================================================================
    # STATISTICS TABLE
    # =========================================================================
    
    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    
    with st.expander("📋 Detailed Statistics", expanded=False):
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
    
    st.toast(f"Analytics loaded for {selected_tf}", icon="📊")


if __name__ == "__main__":
    main()
