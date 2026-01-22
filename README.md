# 📊 Investment Analysis Dashboards

A multi-page Streamlit application for fundamental and technical stock analysis with pattern detection capabilities.

## 🚀 Quick Start

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. (Optional) Create a `.env` file with your API keys:
```
SERPAPI_KEY=your_serpapi_key_here
OPENAI_API_KEY=your_openai_api_key_here
```

3. Run the application:
```bash
streamlit run app.py
```

## 🛠️ Core Dashboards

- **Fundamentals**: Comprehensive company analysis with financial metrics, growth projections, and investment recommendations
- **Technical Analysis**: Interactive price charts with SMA indicators and support/resistance levels
- **Report Charts**: Browse and analyze saved report charts from previous scans
- **Market Analysis**: Compare market indicators, commodities, and economic data across multiple timeframes
- **Scanner Logs**: View scanner execution logs and results

## 🔍 Stock Scanner

Pattern detection system that scans tickers for breakout patterns and generates analysis reports.

**Scan all tickers:**
```bash
python stock_scanner/scanner.py
```

**Test a single ticker:**
```bash
python stock_scanner/test_single_ticker.py TICKER
```

Example:
```bash
python stock_scanner/test_single_ticker.py AAPL
```

## ⚙️ Configuration

All scanner parameters, thresholds, and scoring algorithms are controlled via `config/settings.yaml`.

## ⚠️ Disclaimer

This tool is for educational purposes only and should not be considered as financial advice. Always conduct your own research and consult with a qualified financial advisor. Past performance does not guarantee future results.
