import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
from datetime import datetime
import numpy as np
import locale
import yfinance as yf # Import yfinance

# Streamlit page configuration
st.set_page_config(
    page_title="Samhita : ETF Portfolio Analytics",
    layout="wide",
    page_icon="📊"
)

# --- Premium Professional CSS (Ported from quo.py) ---
def load_css():
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
        
        :root {
            /* QUO/Arthagati Product Family Theme */
            --primary-color: #FFC300;
            --primary-rgb: 255, 195, 0;
            --background-color: #0F0F0F; /* Deep Dark Background */
            --secondary-background-color: #1A1A1A; /* Main Surface/Sidebar */
            --bg-card: #1A1A1A; /* Card Background */
            --bg-elevated: #2A2A2A; /* Table Header/Hover */
            --text-primary: #EAEAEA; /* Light Text */
            --text-secondary: #EAEAEA;
            --text-muted: #888888; /* Muted Text/Dividers */
            --border-color: #2A2A2A;
            --border-light: #3A3A3A;
            
            --success-green: #10b981; /* Green for gains */
            --success-dark: #059669;
            --danger-red: #ef4444; /* Red for losses/danger */
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
        
        .block-container {
            padding-top: 1rem;
            max-width: 1400px;
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
            margin-top: 2.5rem;
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
            font-size: 2.50rem;
            font-weight: 700;
            color: var(--text-primary);
            letter-spacing: -0.50px;
            position: relative;
        }
        
        .premium-header .tagline {
            color: var(--text-muted);
            font-size: 1rem;
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
            font-size: 0.8rem;
            margin-bottom: 0.5rem;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .metric-card h2 {
            color: var(--text-primary);
            font-size: 2rem;
            font-weight: 700;
            margin: 0;
            line-height: 1;
        }
        
        .metric-card .sub-metric {
            font-size: 0.8rem;
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
            background: var(--bg-elevated); /* Lighter card background */
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
        
        /* Table Styling matching quo.py */
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
            gap: 8px;
            background: transparent;
            padding: 0;
            margin-top: 2rem;
            margin-bottom: 1.5rem;
            border-bottom: 1px solid var(--border-color);
        }
        
        .stTabs [data-baseweb="tab"] {
            padding: 0.75rem 1.25rem;
            border-radius: 8px 8px 0 0;
            background: var(--bg-elevated);
            color: var(--text-muted);
            font-weight: 600;
            transition: all 0.2s ease;
        }
        
        .stTabs [aria-selected="true"] {
            background: var(--bg-card) !important;
            color: var(--primary-color) !important;
            border-bottom: 2px solid var(--primary-color);
            margin-bottom: -1px;
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
    </style>
    """, unsafe_allow_html=True)

load_css()

# Function to fetch current prices from yfinance
@st.cache_data(ttl=3600, show_spinner="Fetching real-time prices...")
def fetch_current_prices(symbols):
    """
    Fetches the latest closing price for a list of symbols with the .NS suffix.
    Returns a dictionary of {original_symbol: price}.
    """
    if not symbols:
        return {}

    # Add .NS suffix to symbols and create a unique list of tickers
    tickers_with_suffix = [f"{s}.NS" for s in symbols if s and isinstance(s, str)]
    
    try:
        # Fetch the most recent data for all tickers
        data = yf.download(
            tickers=tickers_with_suffix,
            period="1d",
            interval="1m",
            group_by='ticker',
            progress=False,
            threads=True
        )
        
        prices = {}
        for full_ticker in tickers_with_suffix:
            original_symbol = full_ticker.replace('.NS', '')
            
            if len(tickers_with_suffix) == 1:
                ticker_data = data
            else:
                ticker_data = data.get(full_ticker)
            
            if ticker_data is not None and not ticker_data.empty:
                # Use the last valid close price
                last_price = ticker_data['Close'].iloc[-1]
                prices[original_symbol] = last_price
            else:
                prices[original_symbol] = np.nan # Use NaN if fetch fails

        return prices
    except Exception as e:
        st.error(f"Error fetching current prices via yfinance: {e}")
        return {s: np.nan for s in symbols}


# Function to load data
@st.cache_data
def load_data():
    file_path = "ETF Summary Report.xlsx"
    try:
        df = pd.read_excel(file_path)
        df = df.dropna(how='all')
        df.columns = df.columns.str.strip()
        return df
    except FileNotFoundError:
        st.error(f"File '{file_path}' not found. Please upload the data file.")
        return None

# Function to calculate metrics
def calculate_metrics(df):
    df = df.copy()
    
    # 1. Fetch current prices
    symbols = df['SYMBOL'].tolist()
    price_map = fetch_current_prices(symbols)
    
    # 2. Update CURRENT PRICE column using fetched data
    # Map fetched prices, falling back to existing 'CURRENT PRICE' column if fetch failed (NaN)
    # NOTE: This assumes the input Excel file originally had a 'CURRENT PRICE' column for fallback/initial load
    df['FETCHED PRICE'] = df['SYMBOL'].map(price_map)
    df['CURRENT PRICE'] = df['FETCHED PRICE'].fillna(df.get('CURRENT PRICE', df['AVERAGE PRICE'])) # Use avg price if current price column is missing and fetch failed
    
    # Check for critical missing data after fetch
    if df['CURRENT PRICE'].isnull().any():
        st.warning("⚠️ Some current prices could not be fetched. Using Average Price for calculation.")
    
    # 3. Perform calculations using the updated 'CURRENT PRICE'
    df['INVESTED'] = df['QUANTITY'] * df['AVERAGE PRICE']
    df['CURR. VALUE'] = df['QUANTITY'] * df['CURRENT PRICE']
    df['GAIN'] = df['CURR. VALUE'] - df['INVESTED']
    
    # Avoid division by zero
    df['GAIN %'] = np.where(df['INVESTED'] != 0, df['GAIN'] / df['INVESTED'] * 100, 0)
    
    total_curr_value = df['CURR. VALUE'].sum()
    df['WT'] = np.where(total_curr_value != 0, df['CURR. VALUE'] / total_curr_value * 100, 0)
    df['WEIGHTED RETURN %'] = df['GAIN %'] * df['WT'] / 100  # Weighted return contribution

    metrics = {
        'Total Current Value': total_curr_value,
        'Total Invested': df['INVESTED'].sum(),
        'Total Gain': df['GAIN'].sum(),
        'Portfolio Return %': np.where(df['INVESTED'].sum() != 0, df['GAIN'].sum() / df['INVESTED'].sum() * 100, 0),
        'Top 5 Concentration': df['WT'].nlargest(5).sum(),
        'Number of Holdings': len(df)
    }
    return df, metrics

# Function to format currency (Indian Rupee with Indian comma style)
def format_currency(value):
    # This is a robust fallback for the Indian number system, as locale isn't reliable in Streamlit/hosted environments
    value = float(value)
    negative = value < 0
    value = abs(value)
    
    # Handle the integer part separately
    integer_part = int(value)
    str_value = str(integer_part)[::-1]
    
    grouped = []
    if len(str_value) >= 3:
        grouped.append(str_value[:3])
        str_value = str_value[3:]
        while str_value:
            grouped.append(str_value[:2])
            str_value = str_value[2:]
        formatted = ','.join(grouped[::-1])
    else:
        formatted = str_value[::-1]

    # Handle the decimal part
    decimal_part = round(value - integer_part, 2)
    if decimal_part > 0 or value == 0:
        # Add 2 decimal places, including the leading dot
        formatted += f"{decimal_part:.2f}"[1:]

    formatted = f"{'-' if negative else ''}₹{formatted}"
    return formatted


# Function to create downloadable Excel
def to_excel(df):
    output = BytesIO()
    # Drop calculated columns that may cause issues or are redundant for a base export
    export_df = df.drop(columns=['INVESTED', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT', 'WEIGHTED RETURN %', 'FETCHED PRICE'], errors='ignore')
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        export_df.to_excel(writer, index=False, sheet_name='Portfolio')
    return output.getvalue()

# Main app
def main():
    # Header - Using the premium-header structure
    st.markdown(f"""
        <div class="premium-header">
            <h1>Samhita | ETF Portfolio Insights</h1>
            <div class="tagline">Hemrek Capital • {datetime.now().strftime("%B %d, %Y")}</div>
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
    
    # Metrics in columns
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
        gain_class = 'success' if metrics['Total Gain'] >= 0 else 'danger'
        st.markdown(f"""
            <div class='metric-card {gain_class}'>
                <h4>Absolute Gain/Loss</h4>
                <h2 style='color: var(--{gain_class}-green);'>
                    {format_currency(metrics['Total Gain'])}
                </h2>
                <div class='sub-metric'>Since inception</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        return_class = 'success' if metrics['Portfolio Return %'] >= 0 else 'danger'
        st.markdown(f"""
            <div class='metric-card {return_class}'>
                <h4>Total Return</h4>
                <h2 style='color: var(--{return_class}-green);'>
                    {metrics['Portfolio Return %']:.2f}%
                </h2>
                <div class='sub-metric'>Portfolio XIRR equivalent</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
            <div class='metric-card neutral'>
                <h4>Holdings & Concentration</h4>
                <h2 style='color: var(--text-primary);'>{metrics['Number of Holdings']} Holdings</h2>
                <div class='sub-metric'>Top 5 concentration: {metrics['Top 5 Concentration']:.1f}%</div>
            </div>
        """, unsafe_allow_html=True)
    
    # Tabs for detailed views
    tab1, tab2 = st.tabs(["Performance Analysis", "Portfolio Details"])

    with tab1:
        # Performance Highlights
        st.markdown("""
            <div class='section'>
                <div class='section-header'>
                    <h3 class='section-title'>Performance Highlights</h3>
                    <p class='section-subtitle'>Top and bottom performing assets in your portfolio</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        # Side-by-side layout for Absolute Gain/Loss % and Weighted Return %
        col_metrics1, col_metrics2 = st.columns([1, 1])

        # Section 1: Absolute Gain/Loss %
        with col_metrics1:
            st.markdown("<h3 class='performance-section-header'>Absolute Gain/Loss %</h3>", unsafe_allow_html=True)
            col_out1, col_under1 = st.columns(2)

            with col_out1:
                st.markdown("<h4 class='performance-subheader'>Out-Performers (Highest GAIN %)</h4>", unsafe_allow_html=True)
                top_performers_gain = df.nlargest(3, 'GAIN %')
                for _, row in top_performers_gain.iterrows():
                    # Use CSS variables
                    gain_color = 'success-green' if row['GAIN %'] >= 0 else 'danger-red'
                    weighted_color = 'success-green' if row['WEIGHTED RETURN %'] >= 0 else 'danger-red'
                    
                    st.markdown(f"""
                        <div class='performance-card positive'>
                            <div class='title'>{row['SYMBOL']}</div>
                            <div class='stats'>
                                <span>Gain/Loss</span>
                                <span style='color: var(--{gain_color});'>{row['GAIN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Weighted Return</span>
                                <span style='color: var(--{weighted_color});'>{row['WEIGHTED RETURN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Current Price</span>
                                <span style='color: var(--text-primary);'>{format_currency(row['CURRENT PRICE'])}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            with col_under1:
                st.markdown("<h4 class='performance-subheader'>Under-Performers (Lowest GAIN %)</h4>", unsafe_allow_html=True)
                bottom_performers_gain = df.nsmallest(3, 'GAIN %')
                for _, row in bottom_performers_gain.iterrows():
                    # Use CSS variables
                    gain_color = 'success-green' if row['GAIN %'] >= 0 else 'danger-red'
                    weighted_color = 'success-green' if row['WEIGHTED RETURN %'] >= 0 else 'danger-red'
                    
                    st.markdown(f"""
                        <div class='performance-card {"positive" if row['GAIN %'] >= 0 else "negative"}'>
                            <div class='title'>{row['SYMBOL']}</div>
                            <div class='stats'>
                                <span>Gain/Loss</span>
                                <span style='color: var(--{gain_color});'>{row['GAIN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Weighted Return</span>
                                <span style='color: var(--{weighted_color});'>{row['WEIGHTED RETURN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Current Price</span>
                                <span style='color: var(--text-primary);'>{format_currency(row['CURRENT PRICE'])}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # Section 2: Weighted Return %
        with col_metrics2:
            st.markdown("<h3 class='performance-section-header'>Weighted Return %</h3>", unsafe_allow_html=True)
            col_out2, col_under2 = st.columns(2)

            with col_out2:
                st.markdown("<h4 class='performance-subheader'>Out-Performers (Highest WEIGHTED RETURN %)</h4>", unsafe_allow_html=True)
                top_performers_weighted = df.nlargest(3, 'WEIGHTED RETURN %')
                for _, row in top_performers_weighted.iterrows():
                    # Use CSS variables
                    gain_color = 'success-green' if row['GAIN %'] >= 0 else 'danger-red'
                    weighted_color = 'success-green' if row['WEIGHTED RETURN %'] >= 0 else 'danger-red'
                    
                    st.markdown(f"""
                        <div class='performance-card positive'>
                            <div class='title'>{row['SYMBOL']}</div>
                            <div class='stats'>
                                <span>Gain/Loss</span>
                                <span style='color: var(--{gain_color});'>{row['GAIN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Weighted Return</span>
                                <span style='color: var(--{weighted_color});'>{row['WEIGHTED RETURN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Current Price</span>
                                <span style='color: var(--text-primary);'>{format_currency(row['CURRENT PRICE'])}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

            with col_under2:
                st.markdown("<h4 class='performance-subheader'>Under-Performers (Lowest WEIGHTED RETURN %)</h4>", unsafe_allow_html=True)
                bottom_performers_weighted = df.nsmallest(3, 'WEIGHTED RETURN %')
                for _, row in bottom_performers_weighted.iterrows():
                    # Use CSS variables
                    gain_color = 'success-green' if row['GAIN %'] >= 0 else 'danger-red'
                    weighted_color = 'success-green' if row['WEIGHTED RETURN %'] >= 0 else 'danger-red'
                    
                    st.markdown(f"""
                        <div class='performance-card {"positive" if row['WEIGHTED RETURN %'] >= 0 else "negative"}'>
                            <div class='title'>{row['SYMBOL']}</div>
                            <div class='stats'>
                                <span>Gain/Loss</span>
                                <span style='color: var(--{gain_color});'>{row['GAIN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Weighted Return</span>
                                <span style='color: var(--{weighted_color});'>{row['WEIGHTED RETURN %']:.2f}%</span>
                            </div>
                            <div class='stats'>
                                <span>Current Price</span>
                                <span style='color: var(--text-primary);'>{format_currency(row['CURRENT PRICE'])}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

        # Gain/Loss Distribution Histogram
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
            <div class='section'>
                <div class='section-header'>
                    <h3 class='section-title'>Gain/Loss Distribution</h3>
                    <p class='section-subtitle'>Performance across all holdings by weight rank</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # Sort by weight (WT) in descending order and assign ranks
        sorted_df = df.sort_values('WT', ascending=False).reset_index(drop=True)
        sorted_df['Weight Rank'] = sorted_df.index + 1  # 1-based ranking
        
        # Create bar chart
        fig_gain = go.Figure()
        
        # Calculate bar width based on number of holdings for better aesthetics
        num_holdings = len(sorted_df)
        bar_width = min(0.8, 15 / num_holdings) if num_holdings > 0 else 0.8
        
        # Add Gain/Loss % bars with values on top
        fig_gain.add_trace(go.Bar(
            x=sorted_df['SYMBOL'],
            y=sorted_df['GAIN %'],
            name='Gain/Loss %',
            # Use CSS variable colors for markers
            marker_color=['#10b981' if x >= 0 else '#ef4444' for x in sorted_df['GAIN %']],
            text=[f"{x:.2f}%" for x in sorted_df['GAIN %']],
            textposition='outside',
            textfont=dict(color='#EAEAEA', size=12),
            width=bar_width
        ))
        
        # Dynamic scaling for y-axis with extra padding for outside labels
        gain_min = sorted_df['GAIN %'].min()
        gain_max = sorted_df['GAIN %'].max()
        padding = max(abs(gain_min), abs(gain_max)) * 0.1  # 10% padding
        extra_label_space = (gain_max - gain_min) * 0.1 if gain_max > 0 else 0
        y_range = [gain_min - padding, gain_max + padding + extra_label_space]
        
        fig_gain.update_layout(
            template='plotly_dark', # Use dark theme template
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color="#EAEAEA"),
            margin=dict(l=0, r=0, t=20, b=0),
            xaxis=dict(
                gridcolor='rgba(255,255,255,0.1)', 
                title='Symbol (Ordered by Weight Rank)',
                tickangle=45,
                showgrid=False
            ),
            yaxis=dict(
                gridcolor='rgba(255,255,255,0.05)', 
                title='Gain/Loss (%)',
                range=y_range
            ),
            showlegend=False,
            height=500,
            bargap=0.15
        )
        st.plotly_chart(fig_gain, use_container_width=True)

        # Portfolio Composition Treemap
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.markdown("""
            <div class='section'>
                <div class='section-header'>
                    <h3 class='section-title'>Portfolio Composition</h3>
                    <p class='section-subtitle'>Asset allocation by current value</p>
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        # --- LOGIC FOR DYNAMIC COLOR SCALE ---
        min_gain_pct = df['GAIN %'].min()
        max_gain_pct = df['GAIN %'].max()
        
        color_scale_config = {}
        
        if min_gain_pct >= 0:
            # All positive: Sequential scale (Gold/Amber to Green)
            color_scale_config['color_continuous_scale'] = ['#FFC300', '#10b981']
            color_scale_config['range_color'] = [min_gain_pct, max_gain_pct]
        elif max_gain_pct <= 0:
            # All negative: Sequential scale (Red to Darker Red)
            color_scale_config['color_continuous_scale'] = ['#f87171', '#ef4444']
            color_scale_config['range_color'] = [min_gain_pct, max_gain_pct]
        else:
            # Mixed: Diverging scale centered at 0 (Red -> Gold/Neutral -> Green)
            color_scale_config['color_continuous_scale'] = ['#ef4444', '#FFC300', '#10b981']
            color_scale_config['color_continuous_midpoint'] = 0
        # --- END OF NEW LOGIC ---
        
        fig_treemap = px.treemap(
            df,
            path=['SYMBOL'],
            values='CURR. VALUE',
            color='GAIN %',
            **color_scale_config 
        )
        fig_treemap.update_layout(
            margin=dict(t=0, l=0, r=0, b=0),
            paper_bgcolor='rgba(0,0,0,0)',
            font_color='#EAEAEA'
        )
        st.plotly_chart(fig_treemap, use_container_width=True)

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
        
        # Format columns using CSS variables for colors
        display_df['AVERAGE PRICE'] = display_df['AVERAGE PRICE'].apply(format_currency)
        display_df['INVESTED'] = display_df['INVESTED'].apply(format_currency)
        
        # Display the real-time fetched price
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
        
        # Reorder columns
        display_cols = ['RANK', 'ASSET NAME', 'SYMBOL', 'QUANTITY', 'AVERAGE PRICE', 'CURRENT PRICE', 
                       'INVESTED', 'CURR. VALUE', 'GAIN', 'GAIN %', 'WT']
        display_df = display_df[display_cols]
        
        # Display table with HTML styling, using the table-container wrapper
        st.markdown(f"""
            <div class='table-container'>
                <table class='table'>
                    {display_df.to_html(escape=False, index=False, classes='table')}
                </table>
            </div>
        """, unsafe_allow_html=True)
        
        # Export button for convenience in this tab too
        excel_data = to_excel(df)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
        st.download_button(
            "Export Raw Portfolio Data (Excel)",
            excel_data,
            file_name=f"samhita_portfolio_details_{datetime.now().strftime('%Y%m%d')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheet.sheet",
            use_container_width=False
        )


if __name__ == "__main__":
    import base64 # Import base64 for the export link in col5
    main()
