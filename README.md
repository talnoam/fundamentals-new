# Fundamentals Investment Dashboard

A comprehensive Streamlit dashboard for fundamental analysis of stocks, designed for long-term investment decisions (3-5 years).

## Features

- **Interactive Dashboard**: User-friendly interface for analyzing any stock ticker
- **Comprehensive Stock Selection**:
  - Dropdown selection from S&P 500, NASDAQ-100, and Dow Jones companies
  - Search functionality with major indices and popular stocks
  - Custom ticker input for any stock symbol
- **Comprehensive Analysis**: 
  - Historical financial data and trends
  - Growth rate calculations
  - Future price projections
  - Intrinsic value estimation
  - Risk assessment
- **Interactive Price Charts**:
  - Candlestick charts with OHLC (Open, High, Low, Close) data
  - Volume analysis charts
  - Multiple timeframes: Daily, Weekly, Monthly
  - Interactive zoom, pan, and hover functionality
  - Chart data spans the analysis period (years_to_estimate)
- **Investment Metrics**:
  - P/E ratios
  - Discount rates
  - Margin of safety
  - Expected returns
- **Persistent Analysis**: Session state keeps analysis results when changing chart timeframes
- **Investment Recommendations**: Buy/Hold/Avoid signals based on analysis

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

### Running the Dashboard

```bash
streamlit run dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

### Using the Dashboard

1. **Select a Stock**: 
   - Choose from the dropdown list of major stocks (S&P 500, NASDAQ-100, Dow Jones)
   - Or enter any custom ticker symbol
2. **Set Parameters**: 
   - Adjust investment timeline (3-5 years)
   - Set margin of safety (5-30%)
3. **Analyze**: Click "Analyze Company" to generate the full report
4. **Review Results**: 
   - Key metrics and company information
   - Buy/Hold/Avoid recommendation
   - Detailed financial analysis with percentage changes
   - Risk assessment factors
   - Investment summary with projected returns
5. **Interactive Charts**:
   - View candlestick price charts below the analysis
   - Switch between Daily, Weekly, and Monthly timeframes
   - Analyze volume patterns and price movements
   - Charts automatically update based on your analysis period

### Chart Features

- **Candlestick Charts**: Visual representation of price movements with open, high, low, and close prices
- **Volume Analysis**: Bar chart showing trading volume for correlation with price movements
- **Timeframe Options**:
  - **Daily**: Best for short-term analysis (limited to 1 year for performance)
  - **Weekly**: Ideal for medium-term trend analysis (default)
  - **Monthly**: Perfect for long-term pattern recognition
- **Interactive Features**: Zoom, pan, hover for detailed data points
- **Persistent State**: Analysis results remain visible when switching chart timeframes

### Running the Original Script

You can also run the original command-line version:

```bash
python report.py
```

## Key Components

- `dashboard.py`: Streamlit web interface with chart functionality
- `report.py`: Core analysis logic and candlestick chart creation
- `report_utils.py`: Financial calculations, data fetching, and ticker management

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