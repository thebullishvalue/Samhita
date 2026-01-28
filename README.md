# SAMHITA (संहिता) - Portfolio Tracker

**A Hemrek Capital Product | v1.1.0**

Real-time ETF portfolio analytics with institutional-grade performance tracking and benchmark comparison.

## Features

### Dashboard Mode

#### 📊 Performance Analysis Tab
- **Performance Snapshot**: Total P&L, Win Rate, Avg Winner/Loser, Best/Worst Performer
- **Top Movers**: Side-by-side view of Top 5 Gainers and Losers
- **Risk-Return Profile**: Scatter plot of Return vs Weight (bubble size = value)
- **Return Attribution**: Waterfall chart showing contribution to total return
- **Portfolio Composition**: Value-weighted treemap with gain/loss coloring

#### 📋 Portfolio Details Tab
- Complete holdings table with all metrics
- Export functionality
- Search and sort capabilities

#### 🎯 Holdings Analytics Tab (Institutional Grade)
- **Concentration Metrics**: HHI, Effective N, Gini Coefficient, Top 5/10 concentration
- **Performance Distribution**: Win rate, average/median returns, dispersion
- **Weight Distribution Treemap**: Visualize position sizes
- **Lorenz Curve**: Concentration curve vs equal weight
- **Risk & Return Contribution**: Dual horizontal bar chart

### Analysis Mode (Bloomberg Terminal Grade)
- **Interactive Chart**: Portfolio vs NIFTY 50 benchmark (data pegged to market dates)
- **Timeframe Buttons**: 1W, 1M, 3M, 6M, YTD, 1Y, 2Y, 5Y, MAX
- **Risk-Adjusted Metrics**: 
  - Sharpe, Sortino, Calmar, Information Ratio, Treynor
  - Alpha, Beta, R-Squared, Correlation
  - VaR (95%, 99%), CVaR, Tracking Error
  - Up/Down Capture Ratios
- **Drawdown Analysis**: Underwater equity curve with max DD marker
- **Returns Distribution**: Histogram with VaR overlay
- **Rolling Analytics**: Dynamic window rolling Sharpe and Beta
- **Monthly Heatmap**: Year × Month returns matrix with YTD
- **Holding Attribution**: Individual contribution to portfolio return

## Installation

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Requirements

- Python 3.10+
- streamlit
- pandas
- numpy
- plotly
- yfinance
- openpyxl

## Data Input

Place your portfolio data in `ETF Summary Report.xlsx` with columns:
- ASSET NAME
- SYMBOL (NSE ticker without .NS suffix)
- QUANTITY
- AVERAGE PRICE

## Hemrek Capital Design System

- Golden accent theme (#FFC300)
- Dark mode interface
- Consistent with NIRNAY, AARAMBH, ARTHAGATI, PRAGYAM
- Dynamic IST footer timestamp

## Version History

- v1.1.0: Institutional-grade analytics, benchmark comparison, advanced metrics
- v1.0.0: Initial release
# Samhita
