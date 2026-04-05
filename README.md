# SAMHITA (संहिता) - Portfolio Tracker

**A @thebullishvalue Product | v1.1.1**

Real-time ETF portfolio analytics with institutional-grade performance tracking, benchmark comparison, and advanced risk analytics.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
  - [Dashboard Mode](#dashboard-mode)
  - [Analysis Mode](#analysis-mode)
- [Installation](#installation)
- [Usage](#usage)
- [Data Input](#data-input)
- [Configuration](#configuration)
- [Dependencies](#dependencies)
- [System Requirements](#system-requirements)
- [Version History](#version-history)

---

## Overview

SAMHITA (संहिता) is a professional-grade portfolio tracking application built with Streamlit. It provides two distinct operating modes to serve different user needs:

- **Dashboard Mode**: Quick portfolio overview with performance metrics, top movers, concentration analytics, and interactive visualizations
- **Analysis Mode**: Bloomberg Terminal-style analytics with benchmark comparison (NIFTY 50), risk-adjusted metrics, rolling analytics, and attribution analysis

The application fetches real-time prices from Yahoo Finance, processes portfolio data from an Excel file, and renders institutional-grade analytics with a premium dark-theme UI featuring a gold accent design system.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        SAMHITA Application                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────────┐         ┌──────────────────────────┐   │
│  │  Data Sources    │         │   UI Layer               │   │
│  │                  │         │                          │   │
│  │  • Excel File    │         │  • Dashboard Mode        │   │
│  │  • Yahoo Finance │         │  • Analysis Mode         │   │
│  │                  │         │                          │   │
│  └────────┬─────────┘         └──────────┬───────────────┘   │
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
│  ┌──────────────────┐         ┌──────────────────────────┐   │
│  │  Metrics Engine  │────────►│  Visualization Layer     │   │
│  │                  │         │                          │   │
│  │  • Portfolio     │         │  • Metric Cards          │   │
│  │    Calculations  │         │  • Interactive Charts    │   │
│  │  • Risk Metrics  │         │  • Tables & Heatmaps     │   │
│  │  • Benchmark     │         │  • Export Functions      │   │
│  │    Comparison    │         │                          │   │
│  └──────────────────┘         └──────────────────────────┘   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Core Modules

| Module | Description |
|---|---|
| **Data Fetching Layer** | Real-time price retrieval via yfinance with 5-minute caching, handles NSE suffix mapping and holiday alignment |
| **Metrics Calculation Engine** | Portfolio-level P&L, weights, returns, risk-adjusted ratios (Sharpe, Sortino, Calmar, etc.), benchmark-relative metrics (Alpha, Beta, R²) |
| **Visualization Layer** | Interactive Plotly charts (treemaps, heatmaps, scatter plots, waterfall charts), formatted HTML tables, downloadable Excel exports |
| **UI Orchestration** | Streamlit-based sidebar controls, tab navigation, metric cards, timeframe selectors, anchor date configuration |

### Data Flow

1. **Input**: Portfolio data loaded from `ETF Summary Report.xlsx` (asset names, symbols, quantities, average prices)
2. **Price Enrichment**: Real-time current prices and previous close fetched from Yahoo Finance
3. **Metrics Calculation**: Per-holding and portfolio-level metrics computed (values, gains, weights, returns)
4. **Mode Selection**: User chooses Dashboard or Analysis Mode via sidebar
5. **Visualization**: Interactive charts and tables rendered with premium dark-theme styling
6. **Analysis Mode** (optional): Historical data fetched, benchmark comparison computed, advanced analytics rendered

---

## Features

### Dashboard Mode

Comprehensive portfolio overview with three organized tabs:

#### 📊 Performance Analysis
- **Performance Snapshot**: Total P&L, Win Rate, Average Winner/Loser, Best/Worst Performer
- **Top Movers**: Side-by-side horizontal bar charts showing Top 5 Gainers and Losers
- **Risk-Return Profile**: Scatter plot of Return vs Weight (bubble size = current value) with quadrant lines
- **Return Attribution**: Waterfall chart showing each holding's contribution to total portfolio return
- **Portfolio Composition**: Value-weighted treemap with gain/loss coloring

#### 📋 Portfolio Details
- Complete holdings table with rank, asset names, symbols, quantities, prices, values, and returns
- Indian Rupee formatting (lakhs/crores style) with color-coded gains/losses
- Export functionality to download raw portfolio data as Excel file

#### 🎯 Holdings Analytics
- **Concentration Metrics**: HHI, Effective N, Gini Coefficient, Top 5/10 concentration percentages
- **Performance Distribution**: Win rate, average/median returns, return dispersion (standard deviation)
- **Weight Distribution Treemap**: Visualize position sizes with gain/loss coloring
- **Lorenz Curve**: Concentration curve visualization vs equal-weight reference line
- **Risk & Return Contribution**: Dual horizontal bar chart showing return contribution and risk weight

### Analysis Mode

Bloomberg Terminal-grade institutional analytics with NIFTY 50 benchmark comparison:

#### Timeframe Selection
- Interactive timeframe buttons: 1W, 1M, 3M, 6M, YTD, 1Y, 2Y, 5Y, MAX
- Custom anchor date support for metrics calculated from a specific start date

#### Risk-Adjusted Performance Metrics
- **Return Metrics**: Period Return, CAGR, Annualized Volatility, Daily Volatility
- **Risk-Adjusted Ratios**: Sharpe, Sortino, Calmar, Information Ratio, Treynor Ratio
- **Tail Risk Measures**: VaR (95%, 99%), CVaR (Expected Shortfall)
- **Distribution Analytics**: Win Rate, Best/Worst Day, Skewness, Kurtosis, Profit Factor

#### Benchmark Comparison (NIFTY 50)
- **Relative Performance**: Portfolio vs NIFTY 50 normalized chart (pegged to 100)
- **Benchmark Metrics**: Alpha, Beta, R-Squared, Correlation, Tracking Error
- **Capture Ratios**: Up Capture and Down Capture for bull/bear market analysis

#### Advanced Analytics
- **Drawdown Analysis**: Underwater equity curve with maximum drawdown marker
- **Returns Distribution**: Histogram of daily returns with VaR overlay
- **Rolling Analytics**: Dynamic window rolling Sharpe Ratio and Beta
- **Monthly Returns Heatmap**: Year × Month returns matrix with YTD column
- **Holding Attribution**: Individual contribution to portfolio return visualization

---

## Installation

```bash
# Clone or download the repository
cd Samhita-main

# Install dependencies
pip install -r requirements.txt

# Run the application
streamlit run samhita.py
```

The application will open in your default web browser at `http://localhost:8501`.

---

## Usage

### Getting Started

1. **Prepare your data**: Create an Excel file named `ETF Summary Report.xlsx` with the required columns
2. **Place the file**: Ensure the Excel file is in the same directory as `samhita.py`
3. **Launch the app**: Run `streamlit run samhita.py`
4. **View your portfolio**: The app will automatically fetch real-time prices and calculate metrics

### Sidebar Controls

- **REFRESH PRICES**: Clear cached prices and fetch fresh data from Yahoo Finance
- **View Mode**: Switch between Dashboard and Analysis Mode
- **Anchor Date**: Enable custom start date for Analysis Mode metrics (optional)

### Dashboard Mode Tabs

- **Performance Analysis**: Quick overview of portfolio performance with interactive charts
- **Portfolio Details**: Detailed holdings table with export capability
- **Holdings Analytics**: Concentration and diversification metrics

### Analysis Mode

- Select a timeframe using the buttons (or enable anchor date for custom range)
- Review the normalized performance chart vs NIFTY 50
- Analyze risk-adjusted metrics, benchmark comparison, and attribution analysis
- Explore rolling analytics, monthly heatmap, and detailed statistics

---

## Data Input

Place your portfolio data in `ETF Summary Report.xlsx` with the following columns:

| Column | Description | Example |
|---|---|---|
| **ASSET NAME** | Full name of the ETF | "NIFTY 50 ETF" |
| **SYMBOL** | NSE ticker symbol (without .NS suffix) | "NIFTYBEES" |
| **QUANTITY** | Number of units held | 150 |
| **AVERAGE PRICE** | Average purchase price per unit | 185.50 |

**Note**: The `CURRENT PRICE` column is automatically fetched from Yahoo Finance (NSE exchange) at runtime.

---

## Configuration

### Constants

The application uses the following configuration constants (defined at the top of `samhita.py`):

| Constant | Value | Description |
|---|---|---|
| `VERSION` | `v1.1.1` | Application version |
| `BENCHMARK_TICKER` | `^NSEI` | NIFTY 50 index ticker for benchmark comparison |
| `RISK_FREE_RATE` | `6.5%` | Annualized risk-free rate used in Sharpe/Sortino calculations |
| `CACHE_TTL` | `300s` | Cache duration for price fetching functions |

### Customization

- **Theme Colors**: Modify CSS variables in `load_css()` function (line ~38) to change the design system colors
- **Benchmark**: Change `BENCHMARK_TICKER` and `BENCHMARK_NAME` constants to compare against a different index
- **Data File**: Update the `file_path` variable in `load_data()` function to use a different Excel file

---

## Dependencies

| Package | Purpose |
|---|---|
| **streamlit** | Web application framework, caching, UI components |
| **pandas** | DataFrame operations, time series manipulation, resampling |
| **numpy** | Numerical operations (percentiles, covariance, standard deviation) |
| **plotly** | Interactive charting (bar, scatter, treemap, heatmap, line, histogram) |
| **yfinance** | Market data fetching (real-time prices, historical daily data from NSE) |
| **openpyxl** | Excel file reading (input) and writing (export) |

All dependencies are listed in `requirements.txt`. Install with `pip install -r requirements.txt`.

---

## System Requirements

- **Python**: 3.10 or higher
- **Operating System**: macOS, Linux, or Windows
- **Memory**: 2GB RAM minimum (4GB recommended for large portfolios)
- **Network**: Internet connection required for Yahoo Finance data fetching
- **Browser**: Modern web browser (Chrome, Firefox, Safari, Edge)

---

## @thebullishvalue Design System

- **Golden accent theme** (#FFC300) with dark mode interface
- **Consistent branding** across @thebullishvalue products (NIRNAY, AARAMBH, ARTHAGATI, PRAGYAM)
- **Premium UI components**: Metric cards, performance cards, styled tables, and custom CSS
- **Dynamic IST footer timestamp** for real-time awareness

---

## Version History

### v1.1.1 (2026-04-05)
- Code quality improvements with comprehensive type hints
- Modernized import organization following PEP 8 standards
- Removed dead code and unused imports
- Fixed installation command in documentation
- Enhanced function documentation with clear docstrings

### v1.1.0
- Institutional-grade analytics engine with 30+ performance metrics
- NIFTY 50 benchmark comparison with Alpha, Beta, R-Squared, Tracking Error
- Advanced risk metrics: Sharpe, Sortino, Calmar, VaR, CVaR, Information Ratio
- Rolling analytics (Sharpe and Beta with dynamic windows)
- Monthly returns heatmap with YTD column
- Drawdown analysis with underwater equity curve
- Holding attribution analysis

### v1.0.0
- Initial release with portfolio tracking and basic analytics
- Real-time price fetching from Yahoo Finance
- Dashboard mode with performance analysis and holdings analytics
- Excel data import and export functionality
