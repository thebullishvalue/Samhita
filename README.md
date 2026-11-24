<div align="center">

# SAMHITA

**संहिता**

Portfolio Tracker · Live Prices · Performance · Risk

[![Version](https://img.shields.io/badge/version-2.0.24-2B5FD9)](CHANGELOG.md) [![Python](https://img.shields.io/badge/python-3.10%2B-3776AB)](requirements.txt) [![Streamlit](https://img.shields.io/badge/streamlit-1.51.0-FF4B4B)](requirements.txt) [![License](https://img.shields.io/badge/license-proprietary-6B7280)](LICENSE) [![Pragyam Family](https://img.shields.io/badge/pragyam-family-0F1217)](#the-pragyam-family)

</div>

> Your portfolio, priced from a four-tier chain of market sources and read against the NIFTY 50:
> what it holds, what it has earned, and what it risks.

## Overview

SAMHITA (संहिता) is a portfolio tracker built with Streamlit. It reads holdings from
`Summary Report.xlsx`, prices them live and renders the book two ways:

- **Dashboard Mode**: the portfolio at a glance: performance, top movers, concentration and
  composition.
- **Analysis Mode**: the portfolio against the NIFTY 50 over any window: risk-adjusted returns,
  benchmark statistics, drawdowns, rolling analytics and attribution.

Prices resolve through four tiers, each asked only for the symbols the tiers above it could not
price: a Yahoo Finance batch quote, Yahoo batch history, the NSE and BSE end-of-day bhavcopy, and
per-symbol live quotes. Every fetch is traced in the terminal.

## What It Does

### Dashboard Mode

Comprehensive portfolio overview with three organized tabs:

#### Performance Analysis
- **Performance Snapshot**: Total P&L, Win Rate, Average Winner/Loser, Best/Worst Performer
- **Top Movers**: Side-by-side horizontal bar charts showing Top 5 Gainers and Losers
- **Risk-Return Profile**: Scatter plot of Return vs Weight (bubble size = current value) with quadrant lines
- **Return Attribution**: Waterfall chart showing each holding's contribution to total portfolio return
- **Portfolio Composition**: Value-weighted treemap with gain/loss coloring

#### Portfolio Details
- Complete holdings table with rank, asset names, symbols, quantities, prices, values, and returns
- Indian Rupee formatting (lakhs/crores style) with color-coded gains/losses
- Export functionality to download raw portfolio data as Excel file

#### Holdings Analytics
- **Concentration Metrics**: HHI, Effective N, Gini Coefficient, Top 5/10 concentration percentages
- **Performance Distribution**: Win rate, average/median returns, return dispersion (standard deviation)
- **Weight Distribution Treemap**: Visualize position sizes with gain/loss coloring
- **Lorenz Curve**: Concentration curve visualization vs equal-weight reference line
- **Risk & Return Contribution**: Dual horizontal bar chart showing return contribution and risk weight

### Analysis Mode

Institutional analytics with NIFTY 50 benchmark comparison:

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

## Quick Start

```bash
pip install -r requirements.txt
streamlit run samhita.py
```

Put your holdings in `Summary Report.xlsx` beside `samhita.py` (the columns are in the
[guide](docs/GUIDE.md#data-input)). The app opens at `http://localhost:8501`.

## Project Structure

```
samhita.py          the app: data layer (the four price tiers), metrics, both modes
logger_config.py    the family console
ui/                 theme.css + theme.py (the family design system), components
Summary Report.xlsx the portfolio's holdings (the app's input)
.streamlit/         server settings and the theme base
```

## Documentation

| Document | What it covers |
|---|---|
| [Guide](docs/GUIDE.md) | Architecture and data flow, using each mode, the input file, configuration, dependencies, requirements |
| [Changelog](CHANGELOG.md) | Every release, newest first |

## The Pragyam Family

Eleven Streamlit applications built on one design system and one set of components, so a
panel, a table, a chart or a number reads the same in each.

| Product | What it is |
|---|---|
| [**Tattva**](https://github.com/thebullishvalue/Tattva) | Cross-asset fair value, with a call only where its own record supports one |
| [**Nishkarsh**](https://github.com/thebullishvalue/Nishkarsh) | Nifty 50 inference: a top-down forecast and bottom-up breadth, read as one |
| [**Arthagati**](https://github.com/thebullishvalue/Arthagati) | Valuation-anchored market sentiment, tested on data it never saw |
| [**Vyapti**](https://github.com/thebullishvalue/Vyapti) | Market breadth: where participation stands, which way it moves, and what that has meant |
| [**Pragyam**](https://github.com/thebullishvalue/Pragyam) | Portfolio curation that spreads risk rather than predicting returns |
| [**Sanket**](https://github.com/thebullishvalue/Sanket) | A market signal screener: what fired, what is about to, and whether it has paid |
| [**Vaaydo**](https://github.com/thebullishvalue/Vaaydo) | An F&O trade screener on option positioning, with futures tickets |
| [**Anumaan**](https://github.com/thebullishvalue/Indicator) | A chart terminal: calibrated risk, stops and exposure, audited on the chart it is on |
| [**Nivesa**](https://github.com/thebullishvalue/Nivesa) | A bond portfolio ledger: cost, yield, duration and cashflows across accounts |
| **Samhita** · *this repository* | A portfolio tracker: live prices, performance and risk against the benchmark |
| [**Swing**](https://github.com/thebullishvalue/Swing) | A portfolio tracker for the swing book, on the same engine as Samhita |

## License

Proprietary. © 2026 @thebullishvalue. All rights reserved. The source is visible here
for reference only: viewing it grants no right to use, copy, modify or distribute it.
See [LICENSE](LICENSE).

## Disclaimer

Samhita is a research and decision-support tool, not investment advice. Nothing it shows is
a recommendation to buy or sell any security, and past or measured results do not guarantee
future ones. Every decision made with it is your own.

---

<div align="center"><sub>© 2026 @thebullishvalue · Part of the Pragyam product family</sub></div>
