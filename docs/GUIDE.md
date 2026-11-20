# Samhita · Guide

How Samhita is built, how to use each mode, what it reads and how to configure it. The
[README](../README.md) is the overview; this is the detail.

## Architecture

```
┌───────────────────────────────────────────────────────────────┐
│                        SAMHITA Application                    │
├───────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────────────┐    │
│  │  Data Sources    │         │   UI Layer               │    │
│  │                  │         │                          │    │
│  │  • Excel File    │         │  • Dashboard Mode        │    │
│  │  • Yahoo Finance │         │  • Analysis Mode         │    │
│  │    (primary)     │         │                          │    │
│  │  • NSE/BSE       │         │                          │    │
│  │    fallback      │         │                          │    │
│  └────────┬─────────┘         └──────────┬───────────────┘    │
│           │                               │                   │
│           ▼                               │                   │
│  ┌──────────────────┐                     │                   │
│  │  Data Fetching   │                     │                   │
│  │  Layer           │                     │                   │
│  │                  │                     │                   │
│  │  • Current       │◄────────────────────┘                   │
│  │    Prices        │                                         │
│  │  • Previous      │                                         │
│  │    Close         │                                         │
│  │  • Historical    │                                         │
│  │    Data          │                                         │
│  └────────┬─────────┘                                         │
│           │                                                   │
│           ▼                                                   │
│  ┌──────────────────┐         ┌──────────────────────────┐    │
│  │  Metrics Engine  │────────►│  Visualization Layer     │    │
│  │                  │         │                          │    │
│  │  • Portfolio     │         │  • Metric Cards          │    │
│  │    Calculations  │         │  • Interactive Charts    │    │
│  │  • Risk Metrics  │         │  • Tables & Heatmaps     │    │
│  │  • Benchmark     │         │  • Export Functions      │    │
│  │    Comparison    │         │                          │    │
│  └──────────────────┘         └──────────────────────────┘    │
│                                                               │
└───────────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Description |
|---|---|
| **Data Fetching Layer** | Real-time price retrieval via yfinance (primary) with 5-minute caching, NSE/BSE suffix mapping and holiday alignment. Resilient fallback fills any unpriced symbols from secondary sources — NSE live (NseKit) + EOD bhavcopy (jugaad-data); BSE live + EOD bhavcopy (`bse`) — live-first with an EOD backstop. All diagnostics stream to a curated terminal log |
| **Metrics Calculation Engine** | Portfolio-level P&L, weights, returns, risk-adjusted ratios (Sharpe, Sortino, Calmar, etc.), benchmark-relative metrics (Alpha, Beta, R²) |
| **Visualization Layer** | Interactive Plotly charts (treemaps, heatmaps, scatter plots, waterfall charts), formatted HTML tables, downloadable Excel exports |
| **UI Orchestration** | Streamlit-based sidebar controls, tab navigation, metric cards, timeframe selectors, anchor date configuration |

### Data Flow

1. **Input**: Portfolio data loaded from `Summary Report.xlsx` (asset names, symbols, quantities, average prices)
2. **Price Enrichment**: Real-time current prices and previous close fetched from Yahoo Finance (primary); any symbols Yahoo cannot price are resolved from secondary NSE/BSE sources (live-first, EOD bhavcopy backstop), with anything still unresolved falling back to the holding's average price
3. **Metrics Calculation**: Per-holding and portfolio-level metrics computed (values, gains, weights, returns)
4. **Mode Selection**: User chooses Dashboard or Analysis Mode via sidebar
5. **Visualization**: Interactive charts and tables rendered in the family design system (Paper and Slate appearances)
6. **Analysis Mode** (optional): Historical data fetched, benchmark comparison computed, advanced analytics rendered

## Usage

### Getting Started

1. **Prepare your data**: Create an Excel file named `Summary Report.xlsx` with the required columns
2. **Place the file**: Ensure the Excel file is in the same directory as `samhita.py`
3. **Launch the app**: Run `streamlit run samhita.py`
4. **View your portfolio**: The app will automatically fetch real-time prices and calculate metrics

### Sidebar Controls

- **Refresh Prices**: Clear cached prices and fetch fresh data from Yahoo Finance
- **Mode switch** (Dashboard / Analysis): Switch between the two modes
- **Enable Anchor Date**: A custom start date for Analysis Mode metrics (optional)

### Dashboard Mode Tabs

- **Performance Analysis**: Quick overview of portfolio performance with interactive charts
- **Portfolio Details**: Detailed holdings table with export capability
- **Holdings Analytics**: Concentration and diversification metrics

### Analysis Mode

- Select a timeframe using the buttons (or enable anchor date for custom range)
- Review the normalized performance chart vs NIFTY 50
- Analyze risk-adjusted metrics, benchmark comparison, and attribution analysis
- Explore rolling analytics, monthly heatmap, and detailed statistics

## Data Input

Place your portfolio data in `Summary Report.xlsx` with the following columns:

| Column | Description | Example |
|---|---|---|
| **ASSET NAME** | Full name of the Asset | "NIFTY 50 ETF" |
| **SYMBOL** | Ticker symbol. No suffix → NSE (`.NS` applied automatically); `.BO` suffix → BSE | "NIFTYBEES", "NSDL.BO" |
| **QUANTITY** | Number of units held | 150 |
| **AVERAGE PRICE** | Average purchase price per unit | 185.50 |

**Note**: The `CURRENT PRICE` column is fetched automatically at runtime — Yahoo Finance first, then NSE/BSE secondary sources for any gaps. The symbol convention is unchanged: bare symbols resolve on NSE, `.BO` symbols on BSE.

## Configuration

### Constants

Defined in `samhita.py` (the version lives in `ui/theme.py`):

| Constant | Value | Description |
|---|---|---|
| `BENCHMARK_TICKER` | `^NSEI` | NIFTY 50 index ticker for benchmark comparison |
| `BENCHMARK_NAME` | `NIFTY 50` | The benchmark's display name |
| `RF_RATE` | `6.5%` | Annualised risk-free rate used in the Sharpe and Sortino ratios |

Prices and history are cached for 300 seconds (`@st.cache_data(ttl=300)`).

### Customization

- **Theme**: The design system is `ui/theme.css` and `ui/theme.py`, shared with the rest of the family
- **Benchmark**: Change `BENCHMARK_TICKER` and `BENCHMARK_NAME` constants to compare against a different index
- **Data File**: Update the `file_path` variable in `load_data()` function to use a different Excel file

## Dependencies

| Package | Purpose |
|---|---|
| **streamlit** | Web application framework, caching, UI components |
| **pandas** | DataFrame operations, time series manipulation, resampling |
| **numpy** | Numerical operations (percentiles, covariance, standard deviation) |
| **plotly** | Interactive charting (bar, scatter, treemap, heatmap, line, histogram) |
| **yfinance** | Primary market data fetching (real-time prices, historical daily data, NSE + BSE) |
| **NseKit** | Secondary source — live NSE equity quotes (fallback) |
| **jugaad-data** (≥0.33.1) | Secondary source — NSE EOD bhavcopy (fallback backstop) |
| **bse** | Secondary source — live BSE quotes and BSE EOD bhavcopy (fallback) |
| **openpyxl** | Excel file reading (input) and writing (export) |

All dependencies are listed in `requirements.txt`. Install with `pip install -r requirements.txt`.

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 2GB RAM minimum (4GB recommended for large portfolios)
- **Network**: Internet connection required for Yahoo Finance data fetching
- **Browser**: Modern web browser (Chrome, Firefox, Safari, Edge)
