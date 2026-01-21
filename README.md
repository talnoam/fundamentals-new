# Investment Analysis Dashboards

A comprehensive multi-page Streamlit application for investment analysis, featuring both fundamental and technical analysis dashboards for stock evaluation and long-term investment decisions (3-5 years).

## Features

- **Multi-Page Application**: Unified platform with automatic sidebar navigation
  - Landing page with dashboard overview
  - Fundamentals Dashboard for comprehensive company analysis
  - Technical Analysis Dashboard for price chart analysis
  - Report Charts Dashboard for viewing saved report charts
  - Market Analysis Dashboard for market indicators and economic data
- **Interactive Dashboards**: User-friendly interfaces for analyzing any stock ticker
- **Comprehensive Stock Selection**:
  - Dropdown selection from S&P 500, NASDAQ-100, and Dow Jones companies
  - Search functionality with major indices and popular stocks
  - Custom ticker input for any stock symbol
- **Fundamentals Analysis**: 
  - Historical financial data and trends
  - Growth rate calculations
  - Future price projections
  - Intrinsic value estimation
  - Risk assessment
  - Investment recommendations (Buy/Hold/Avoid)
- **Technical Analysis**:
  - Interactive candlestick charts with OHLC (Open, High, Low, Close) data
  - Volume analysis charts
  - Multiple timeframes: Daily, Weekly, Monthly
  - Historical data visualization (1-10 years)
  - SMA indicators (20, 50, 150, 200 periods)
  - Automatic support and resistance level detection
  - Support/resistance calculated from recent 6 months of data
- **Report Charts**:
  - Browse saved report charts from `reports/charts`
  - Interactive zoom, pan, and hover analysis
  - Filter by ticker and report date
- **Market Analysis**:
  - 12+ market indicators (Bitcoin, S&P 500, NASDAQ, Dow Jones, VIX, etc.)
  - Compare multiple indicators on the same chart
  - Flexible time periods: 1 Day, 7 Days, 1 Month, 6 Months, Year to Date, or Custom (1-10 years)
  - Normalization option for comparing indicators with different price scales
  - Commodities: Gold, Silver, Crude Oil
  - Economic indicators: VIX, 10-Year Treasury, US Dollar Index
- **Interactive Price Charts**:
  - Interactive zoom, pan, and hover functionality
  - Chart data spans the analysis period
- **Investment Metrics**:
  - P/E ratios
  - Discount rates
  - Margin of safety
  - Expected returns
- **Persistent Analysis**: Session state keeps analysis results when navigating between pages

## Installation

1. Clone or download this repository
2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. (Optional) Create a `.env` file with your SerpAPI key for investor relations links:
```
SERPAPI_KEY=your_serpapi_key_here
```

## Usage

### Running the Application

Run the main application (includes all dashboards):
```bash
streamlit run app.py
```

The application will open in your browser at `http://localhost:8501`

### Navigation

The application uses Streamlit's built-in multi-page navigation:
- **Landing Page** (`app.py`): Welcome page with dashboard overview
- **Fundamentals Dashboard** (`pages/Fundamentals.py`): Comprehensive fundamental analysis
- **Technical Analysis Dashboard** (`pages/Technical_Analysis.py`): Price chart analysis with technical indicators
- **Report Charts Dashboard** (`pages/Report_Charts.py`): View and analyze saved report charts
- **Market Analysis Dashboard** (`pages/Market_Analysis.py`): Market indicators and economic data analysis

Navigate between pages using the sidebar menu that appears automatically in multi-page Streamlit apps.

### Using the Application

#### Landing Page
The landing page provides an overview of available dashboards and getting started instructions.

#### Fundamentals Dashboard
1. **Navigate**: Select "Fundamentals" from the sidebar menu
2. **Select a Stock**: 
   - Choose from the dropdown list of major stocks (S&P 500, NASDAQ-100, Dow Jones)
   - Or enter any custom ticker symbol
3. **Set Parameters**: 
   - Adjust investment timeline (3-5 years)
   - Set margin of safety (5-30%)
4. **Analyze**: Click "Analyze Company" to generate the full report
5. **Review Results**: 
   - Key metrics and company information
   - Buy/Hold/Avoid recommendation
   - Detailed financial analysis with percentage changes
   - Risk assessment factors
   - Investment summary with projected returns
6. **Interactive Charts**:
   - View candlestick price charts below the analysis
   - Switch between Daily, Weekly, and Monthly timeframes
   - Analyze volume patterns and price movements
   - Charts automatically update based on your analysis period

#### Technical Analysis Dashboard
1. **Navigate**: Select "Technical_Analysis" from the sidebar menu
2. **Select a Stock**: 
   - Choose from the dropdown list of major stocks (S&P 500, NASDAQ-100, Dow Jones)
   - Or enter any custom ticker symbol
3. **Set Parameters**: 
   - Adjust years of historical data (1-10 years)
4. **Technical Indicators** (Optional):
   - Enable SMA indicators: 20, 50, 150, or 200 periods
   - Toggle support and resistance levels (calculated from recent 6 months)
5. **View Charts**:
   - Interactive candlestick price charts with volume
   - Switch between Daily, Weekly, and Monthly timeframes
   - Analyze price movements and trading volume patterns
   - Overlay SMA lines and support/resistance levels
   - Charts update automatically based on your selected parameters

#### Report Charts Dashboard
1. **Navigate**: Select "Report_Charts" from the sidebar menu
2. **Select a Date**:
   - Choose a specific report date from the dropdown
   - Or select "All dates" to see reports from all dates
3. **Select a Ticker**:
   - Choose from the dropdown list of available report charts (filtered by selected date)
   - Or enter a custom ticker to filter existing reports
4. **Pick a Report**:
   - Select the report chart from the list (sorted by highest score first)
5. **Analyze**:
   - Use interactive zoom, pan, and hover to inspect the chart
   - Review report scores alongside the chart

#### Market Analysis Dashboard
1. **Navigate**: Select "Market_Analysis" from the sidebar menu
2. **Select Market Indicators**: 
   - Choose one or more indicators from the list:
     - Stock Indices: S&P 500, NASDAQ Composite, NASDAQ 100, Russell 2000, Dow Jones
     - Cryptocurrency: Bitcoin
     - Commodities: Gold, Silver, Crude Oil
     - Economic Indicators: VIX, 10-Year Treasury, US Dollar Index
3. **Set Time Period**: 
   - Quick periods: 1 Day, 7 Days, 1 Month, 6 Months, Year to Date
   - Or select "Custom Years" for 1-10 years
4. **View Charts**:
   - **Single Indicator**: Full candlestick chart with SMA and support/resistance options
   - **Multiple Indicators**: Comparison line chart with normalization option
   - Normalize to percentage change for comparing indicators with different price scales
   - Switch between Daily, Weekly, and Monthly timeframes

### Chart Features

- **Candlestick Charts**: Visual representation of price movements with open, high, low, and close prices
- **Volume Analysis**: Bar chart showing trading volume for correlation with price movements
- **Timeframe Options**:
  - **Daily**: Best for short-term analysis
  - **Weekly**: Ideal for medium-term trend analysis
  - **Monthly**: Perfect for long-term pattern recognition
- **Technical Indicators**:
  - **SMA (Simple Moving Averages)**: 20, 50, 150, and 200 period moving averages
  - **Support & Resistance Levels**: Automatically calculated from recent price action (last 6 months)
  - Color-coded indicators for easy identification
- **Multi-Indicator Comparison**:
  - Compare multiple market indicators on the same chart
  - Normalization option shows percentage change from start date
  - Useful for analyzing correlations and relative performance
- **Flexible Time Periods**:
  - Quick access: 1 Day, 7 Days, 1 Month, 6 Months, Year to Date
  - Custom range: 1-10 years
- **Interactive Features**: Zoom, pan, hover for detailed data points
- **Persistent State**: Analysis results remain visible when switching chart timeframes

### Running the Original Script

You can also run the original command-line version:

```bash
python report.py
```

### Stock Scanner

The stock scanner (`stock_scanner/scanner.py`) is a pattern detection system that scans multiple tickers for breakout patterns and generates analysis reports.

#### Running the Full Scanner

To scan all tickers (S&P 500, Dow, Nasdaq):

```bash
python stock_scanner/scanner.py
```

#### Testing a Single Ticker

To test pattern detection and scoring for a single ticker and generate its chart:

```bash
python stock_scanner/test_single_ticker.py TICKER
```

For example:
```bash
python stock_scanner/test_single_ticker.py AAPL
```

This script:
- Analyzes the specified ticker using `analyze_single_ticker`
- Displays pattern detection results (compression, R², breakout status, score)
- Generates an interactive chart using `create_chart` saved to `reports/charts/`
- Useful for examining changes in pattern detector and scoring algorithms

You can also specify a custom config file:
```bash
python stock_scanner/test_single_ticker.py AAPL --config config/settings.yaml
```

## Key Components

- `app.py`: Main entry point and landing page for the multi-page application
- `pages/Fundamentals.py`: Streamlit page for fundamental analysis with chart functionality
- `pages/Technical_Analysis.py`: Streamlit page for technical analysis with SMA and support/resistance indicators
- `pages/Report_Charts.py`: Streamlit page for viewing saved report charts
- `pages/Market_Analysis.py`: Streamlit page for market indicators and economic data analysis
- `report.py`: Core analysis logic, candlestick chart creation, and multi-indicator chart functions
- `report_utils.py`: Financial calculations, data fetching, and ticker management
- `stock_scanner/scanner.py`: Main stock scanner that analyzes multiple tickers for breakout patterns
- `stock_scanner/test_single_ticker.py`: Script to test pattern detection and scoring for a single ticker
- `config/settings.yaml`: Centralized thresholds and scoring parameters for the scanner

## Configuration

The `config/settings.yaml` file contains all configurable parameters for the stock scanner. Key sections include:

### Pattern Detection (`patterns` section)
- `adaptive_windows`: Configuration for adaptive window scanning
  - `start`: Starting window size (default: 40)
  - `end`: Ending window size (default: 360)
  - `step`: Step size between windows (default: 10)
- `order_adjustment`: Dynamic order adjustment based on window size
  - `min_order`: Minimum order value (default: 3)
  - `threshold`: Window size threshold for order adjustment (default: 100)
  - `adjustment`: Order adjustment value for smaller windows (default: -2)
- `selection_scoring`: Parameters for scoring pattern quality
  - `quality_bonus_threshold`: R² threshold for quality bonus (default: 0.8)
  - `quality_bonus_value`: Bonus multiplier for high-quality patterns (default: 1.5)
  - `window_weight_threshold`: Window size threshold for weight adjustment (default: 90)
  - `window_weight_value`: Weight multiplier for smaller windows (default: 1.2)

### Scoring (`scoring` section)
- `final_score_scale`: Multiplier for the final normalized score (default: 100.0)
- `volatility_bonus_scale`: Bonus multiplier for volatility score (default: 10.0)
- `annual_trading_days`: Trading days used for annualized volatility (default: 252)
- `max_annual_volatility`: Volatility cap for full score (default: 0.50)

## Investment Methodology

This tool focuses on fundamental analysis for profitable companies using:

- **Discounted Cash Flow (DCF)** modeling
- **Price-to-Earnings (P/E)** ratio analysis
- **Growth rate** projections based on analyst estimates
- **Risk-adjusted discount rates** based on company characteristics
- **Margin of safety** for conservative valuations

## Important Disclaimers

⚠️ **This tool is for educational purposes only and should not be considered as financial advice.**

- Always conduct your own research
- Consult with a qualified financial advisor
- Past performance does not guarantee future results
- All investments carry risk of loss

## Data Sources

- Financial data: Yahoo Finance (via yfinance)
- Analyst estimates: Yahoo Finance Analysis pages
- Company information: Yahoo Finance API

## Technical Requirements

- Python 3.8+
- Internet connection for real-time data
- Modern web browser for Streamlit interface

## Troubleshooting

- **"No data found"**: Check if the ticker symbol is correct
- **"EPS is negative"**: The tool only analyzes profitable companies
- **Connection errors**: Check your internet connection
- **Missing data**: Some companies may not have complete financial data available 