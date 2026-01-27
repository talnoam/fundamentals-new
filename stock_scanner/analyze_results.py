import logging
import os
import sys
import re
from pathlib import Path
from datetime import datetime, timedelta, time, date
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd
import pytz
import yaml

# Add the parent directory to the Python path
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_loader import DataEngine

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("backtest.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("BacktestAnalyzer")


def get_valid_entry_price(
    ticker_symbol: str,
    html_file_path: str,
    data_engine: Optional[DataEngine] = None,
) -> Tuple[Optional[float], Any, Dict[str, Any]]:
    """
    Determine a valid entry price based on when the HTML analysis report was created.

    Logic:
    1. Read the file's modification time and convert it to US/Eastern (exchange time).
    2. If the timestamp is during regular market hours (Mon–Fri, 09:30–16:00 ET),
       treat the signal as invalid and return (None, error_message).
    3. Compute a reference date:
       - If created after market close (>= 16:00), reference date = same calendar day.
       - If created before market open (< 09:30), reference date = previous calendar day.
       - If created on a weekend, roll back to the last weekday (Friday, etc.).
    4. Fetch a small historical window ending at the reference date using DataEngine
       (which internally uses yfinance). Because yfinance only returns trading days,
       the last available row in that window is the correct last close (handling
       weekends/holidays transparently).

    Returns:
        (entry_price, actual_trade_date, meta) on success, or
        (None, error_message, meta) on failure, where `meta` contains
        debug information such as the scan timestamp in US/Eastern and
        the computed reference date.
    """
    try:
        if not os.path.exists(html_file_path):
            return None, f"{ticker_symbol}: HTML report path does not exist: {html_file_path}", {}

        # 1) File modification time -> US/Eastern
        mtime = os.path.getmtime(html_file_path)
        utc_dt = datetime.fromtimestamp(mtime, tz=pytz.UTC)
        eastern = pytz.timezone("US/Eastern")
        local_dt = utc_dt.astimezone(eastern)

        local_date = local_dt.date()
        local_time = local_dt.time()

        # 2) Market hours validation
        market_open = time(9, 30)
        market_close = time(16, 0)
        is_market_day = local_dt.weekday() < 5  # Mon–Fri

        if is_market_day and market_open <= local_time < market_close:
            # Scan ran while market was trading – treat as invalid for backtest
            meta = {
                "scan_timestamp_et": local_dt,
                "reference_date": None,
            }
            return None, f"{ticker_symbol}: scan ran during market hours ({local_dt.isoformat()})", meta

        # 3) Reference date calculation
        if local_dt.weekday() >= 5:
            # Weekend: roll back to last weekday (typically Friday)
            reference_date = local_date
            while reference_date.weekday() >= 5:
                reference_date -= timedelta(days=1)
        else:
            if local_time >= market_close:
                # After close -> same day
                reference_date = local_date
            else:
                # Before open (and not during market hours due to check above) -> previous day
                reference_date = local_date - timedelta(days=1)

        # 4) Fetch small historical window around the reference date
        if data_engine is None:
            # Fallback DataEngine with default config if not provided
            data_engine = DataEngine({})

        start_date = datetime.combine(reference_date - timedelta(days=10), time(0, 0))
        end_date = datetime.combine(reference_date + timedelta(days=1), time(0, 0))

        df = data_engine.fetch_historical_data_range(
            ticker_symbol,
            start_date=start_date,
            end_date=end_date,
        )

        meta: Dict[str, Any] = {
            "scan_timestamp_et": local_dt,
            "reference_date": reference_date,
        }

        if df is None or df.empty:
            return None, f"{ticker_symbol}: no historical data available around reference date {reference_date}", meta

        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        df = df.sort_index()
        last_row = df.iloc[-1]
        actual_trade_date = df.index[-1]
        entry_price = float(last_row["Close"])

        return entry_price, actual_trade_date, meta
    except Exception as exc:
        logger.error(
            f"{ticker_symbol}: error determining valid entry price from report {html_file_path} - {exc}",
            exc_info=True,
        )
        return None, f"{ticker_symbol}: unexpected error in get_valid_entry_price: {exc}", {}


def parse_filename(filename: str) -> Optional[Dict[str, Any]]:
    """
    Parse filename to extract ticker, date, and score.
    Expected format: TICKER_YYYY-MM-DD_score_XX.html
    
    Args:
        filename: Name of the report file
        
    Returns:
        Dict with ticker, date, and score or None if parsing fails
    """
    try:
        # Pattern: TICKER_YYYY-MM-DD_score_XX.html
        pattern = r'^([A-Z]+)_(\d{4}-\d{2}-\d{2})_score_(\d+)\.html$'
        match = re.match(pattern, filename)
        
        if match:
            ticker = match.group(1)
            date_str = match.group(2)
            score = int(match.group(3))
            
            # Parse date
            analysis_date = datetime.strptime(date_str, '%Y-%m-%d')
            
            return {
                'ticker': ticker,
                'analysis_date': analysis_date,
                'score': score
            }
    except Exception as e:
        logger.warning(f"Failed to parse filename {filename}: {e}")
    
    return None


def calculate_outcome(prices: pd.Series, entry_price: float, 
                      target_profit: float, stop_loss: float) -> Tuple[str, Optional[datetime]]:
    """
    Determine if the trade hit target profit or stop loss first.
    
    Args:
        prices: Series of prices indexed by date
        entry_price: Price at analysis date
        target_profit: Profit target as decimal (e.g., 0.05 for 5%)
        stop_loss: Stop loss as decimal (e.g., 0.03 for 3%)
        
    Returns:
        Tuple of (outcome, exit_date) where outcome is "Success", "Failure", or "Pending"
    """
    target_price = entry_price * (1 + target_profit)
    stop_price = entry_price * (1 - stop_loss)
    
    for date, price in prices.items():
        if price >= target_price:
            return "Success", date
        elif price <= stop_price:
            return "Failure", date
    
    # Neither target nor stop hit yet
    return "Pending", None


def analyze_single_ticker(
    ticker: str,
    analysis_date: datetime,
    score: int,
    data_engine,
    target_profit: float,
    stop_loss: float,
    performance_window_days: int,
    report_path: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Analyze historical performance for a single ticker recommendation.
    
    Args:
        ticker: Stock ticker symbol
        analysis_date: Date when the analysis was performed
        score: Scanner score assigned to this ticker
        data_engine: DataEngine instance for fetching data
        target_profit: Profit target as decimal
        stop_loss: Stop loss as decimal
        performance_window_days: Number of days to track performance
        
    Returns:
        Dict with analysis results or None if data unavailable
    """
    try:
        # Fetch historical data using date range
        # We need: 1 year before analysis_date (for context) + data until today (for future performance)
        start_date = analysis_date - timedelta(days=365)
        end_date = datetime.now()

        df = data_engine.fetch_historical_data_range(ticker, start_date, end_date)

        if df is None or df.empty:
            logger.warning(f"{ticker}: No historical data available")
            return None
        
        # Ensure the index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        
        # Determine entry price / entry date based on when the scan actually ran
        scan_timestamp_et: Optional[datetime] = None
        reference_date: Optional[datetime] = None
        if report_path:
            entry_price, entry_info, meta = get_valid_entry_price(ticker, report_path, data_engine=data_engine)
            if entry_price is None:
                # entry_info is an error message
                logger.warning(entry_info)
                return None
            entry_date = pd.to_datetime(entry_info)
            scan_timestamp_et = meta.get("scan_timestamp_et")
            reference_date = meta.get("reference_date")
        else:
            # Fallback: use close on analysis date or nearest prior date
            analysis_date_ts = pd.Timestamp(analysis_date)
            
            # Get data on or before analysis date
            prior_data = df[df.index <= analysis_date_ts]
            if prior_data.empty:
                logger.warning(f"{ticker}: No data available on or before {analysis_date}")
                return None
            
            entry_price = prior_data.iloc[-1]['Close']
            entry_date = prior_data.index[-1]
            # We don't have a precise scan timestamp here; use N/A in debug columns
        
        # Get future data (after entry date)
        future_data = df[df.index > entry_date]
        
        if future_data.empty:
            logger.warning(f"{ticker}: No data available after {analysis_date}")
            return None
        
        # Limit to performance window
        window_end = entry_date + timedelta(days=performance_window_days)
        window_data = future_data[future_data.index <= window_end]
        
        if window_data.empty:
            logger.warning(f"{ticker}: No data in performance window")
            return None
        
        # Calculate metrics
        prices = window_data['Close']
        
        # Max return
        max_price = prices.max()
        max_return = ((max_price - entry_price) / entry_price) * 100
        max_return_date = prices.idxmax()
        
        # Max drawdown
        min_price = prices.min()
        max_drawdown = ((min_price - entry_price) / entry_price) * 100
        max_drawdown_date = prices.idxmin()
        
        # Current return (most recent price in window or overall)
        current_price = future_data.iloc[-1]['Close'] if not future_data.empty else entry_price
        current_return = ((current_price - entry_price) / entry_price) * 100
        current_date = future_data.index[-1] if not future_data.empty else entry_date
        
        # Determine outcome
        outcome, exit_date = calculate_outcome(prices, entry_price, target_profit, stop_loss)
        
        # Calculate holding period
        if exit_date:
            holding_days = (exit_date - entry_date).days
        else:
            holding_days = (current_date - entry_date).days
        
        # Get ticker index membership (import locally to avoid segfault)
        try:
            from src.ticker_provider import TickerProvider
            ticker_provider = TickerProvider()
            
            # Fetch individual index tickers using the internal methods
            sp500_tickers = set(ticker_provider._fetch_with_cache("sp500", ticker_provider._fetch_sp500))
            nasdaq_tickers = set(ticker_provider._fetch_with_cache("nasdaq", ticker_provider._fetch_nasdaq))
            dow_tickers = set(ticker_provider._fetch_with_cache("dow", ticker_provider._fetch_dow))
            
            indices = []
            if ticker in sp500_tickers:
                indices.append("S&P 500")
            if ticker in nasdaq_tickers:
                indices.append("NASDAQ")
            if ticker in dow_tickers:
                indices.append("DOW")
            
            index_membership = ", ".join(indices) if indices else "Other"
        except Exception as e:
            logger.warning(f"Could not determine index membership for {ticker}: {e}")
            index_membership = "Unknown"
        
        result = {
            'ticker': ticker,
            'analysis_date': analysis_date.strftime('%Y-%m-%d'),
            'entry_date': entry_date.strftime('%Y-%m-%d'),
            'entry_price': round(entry_price, 2),
            'scan_timestamp_et': scan_timestamp_et.isoformat() if isinstance(scan_timestamp_et, datetime) else 'N/A',
            # reference_date is stored as a date in get_valid_entry_price meta
            'reference_date': (
                reference_date.strftime('%Y-%m-%d')
                if isinstance(reference_date, (datetime, date, pd.Timestamp))
                else 'N/A'
            ),
            'score': score,
            'max_return_pct': round(max_return, 2),
            'max_return_date': max_return_date.strftime('%Y-%m-%d'),
            'max_drawdown_pct': round(max_drawdown, 2),
            'max_drawdown_date': max_drawdown_date.strftime('%Y-%m-%d'),
            'current_return_pct': round(current_return, 2),
            'current_date': current_date.strftime('%Y-%m-%d'),
            'outcome': outcome,
            'exit_date': exit_date.strftime('%Y-%m-%d') if exit_date else 'N/A',
            'holding_days': holding_days,
            'index': index_membership
        }
        
        logger.info(f"{ticker}: Score={score}, Outcome={outcome}, Max Return={max_return:.2f}%")
        return result
        
    except Exception as e:
        logger.error(f"{ticker}: Error in analysis - {e}", exc_info=True)
        return None


class BacktestAnalyzer:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.data_engine = DataEngine(self.config.get('data', {}))
        
        backtest_config = self.config.get('backtest', {})
        self.target_profit = backtest_config.get('target_profit', 0.05)
        self.stop_loss = backtest_config.get('stop_loss', 0.03)
        self.min_score_threshold = backtest_config.get('min_score_threshold', 60)
        self.output_csv = backtest_config.get('output_csv', 'reports/backtest_summary.csv')
        self.performance_window_days = backtest_config.get('performance_window_days', 30)
        
        self.max_workers = self.config.get('performance', {}).get('max_workers', 10)

        self.debug_mode = self.config.get('backtest', {}).get('debug_mode', False)
        
    def _load_config(self, path: str) -> Dict:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {path}. Using defaults.")
            return {}
    
    def scan_reports_directory(self, charts_dir: str = "reports/charts") -> List[Dict[str, Any]]:
        """
        Scan the reports/charts directory and extract all valid report metadata.
        
        Args:
            charts_dir: Directory containing report files
            
        Returns:
            List of dicts with ticker, analysis_date, and score
        """
        charts_path = Path(charts_dir)
        if not charts_path.exists():
            logger.error(f"Charts directory not found: {charts_dir}")
            return []
        
        reports = []
        for file_path in charts_path.glob("*.html"):
            parsed = parse_filename(file_path.name)
            if parsed and parsed['score'] >= self.min_score_threshold:
                # Attach the full path so we can use the file's timestamp
                parsed['report_path'] = str(file_path)
                reports.append(parsed)
        
        logger.info(f"Found {len(reports)} reports with score >= {self.min_score_threshold}")
        return reports
    
    def analyze_all_reports(self, reports: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Analyze all reports in parallel using ThreadPoolExecutor.
        
        Args:
            reports: List of report metadata dicts
            
        Returns:
            DataFrame with analysis results
        """
        if not reports:
            logger.warning("No reports to analyze")
            return pd.DataFrame()
        
        results = []
        total = len(reports)

        if self.debug_mode:
            logger.info(f"⚠️  DEBUG MODE: Analyzing {total} reports SEQUENTIALLY (no parallel processing)")
            
            for i, report in enumerate(reports, 1):
                logger.info(f"BACKTEST_PROGRESS: {i}/{total} - Processing {report['ticker']}")
                result = analyze_single_ticker(
                    report['ticker'],
                    report['analysis_date'],
                    report['score'],
                    self.data_engine,
                    self.target_profit,
                    self.stop_loss,
                    self.performance_window_days,
                    report.get('report_path')
                )
                if result:
                    results.append(result)
            
            return pd.DataFrame(results) if results else pd.DataFrame()
        
        logger.info(f"Analyzing {total} reports with {self.max_workers} threads...")
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {
                executor.submit(
                    analyze_single_ticker,
                    report['ticker'],
                    report['analysis_date'],
                    report['score'],
                    self.data_engine,  # Can pass object with threads
                    self.target_profit,
                    self.stop_loss,
                    self.performance_window_days,
                    report.get('report_path')
                ): report['ticker']
                for report in reports
            }
            
            for i, future in enumerate(as_completed(futures), 1):
                result = future.result()
                logger.info(f"BACKTEST_PROGRESS: {i}/{total}")
                if result:
                    results.append(result)
        
        if not results:
            logger.warning("No successful analyses")
            return pd.DataFrame()
        
        df = pd.DataFrame(results)
        return df
    
    def generate_summary(self, df: pd.DataFrame) -> str:
        """
        Generate a markdown summary of backtest results.
        
        Args:
            df: DataFrame with backtest results
            
        Returns:
            Markdown-formatted summary string
        """
        if df.empty:
            return "## No Data Available\n\nNo backtest results to summarize."
        
        # Overall statistics
        total_signals = len(df)
        success_count = (df['outcome'] == 'Success').sum()
        failure_count = (df['outcome'] == 'Failure').sum()
        pending_count = (df['outcome'] == 'Pending').sum()
        
        hit_rate = (success_count / (success_count + failure_count) * 100) if (success_count + failure_count) > 0 else 0
        
        avg_max_return = df['max_return_pct'].mean()
        avg_max_drawdown = df['max_drawdown_pct'].mean()
        avg_current_return = df['current_return_pct'].mean()
        avg_holding_days = df['holding_days'].mean()
        
        # Score correlation
        completed_df = df[df['outcome'].isin(['Success', 'Failure'])]
        if not completed_df.empty:
            score_corr_return = completed_df['score'].corr(completed_df['max_return_pct'])
            avg_score_success = completed_df[completed_df['outcome'] == 'Success']['score'].mean()
            avg_score_failure = completed_df[completed_df['outcome'] == 'Failure']['score'].mean()
        else:
            score_corr_return = 0
            avg_score_success = 0
            avg_score_failure = 0
        
        # Performance by index
        index_stats = df.groupby('index').agg({
            'outcome': lambda x: (x == 'Success').sum() / ((x == 'Success').sum() + (x == 'Failure').sum()) * 100 if ((x == 'Success').sum() + (x == 'Failure').sum()) > 0 else 0,
            'max_return_pct': 'mean',
            'ticker': 'count'
        }).round(2)
        
        # Build markdown summary
        summary = f"""
# 📊 Backtest Analysis Summary

## Overall Performance
- **Total Signals Analyzed**: {total_signals}
- **Completed Trades**: {success_count + failure_count} (Success: {success_count}, Failure: {failure_count})
- **Pending Trades**: {pending_count}
- **Hit Rate**: {hit_rate:.2f}% (using {self.target_profit*100:.0f}% target, {self.stop_loss*100:.0f}% stop)

## Return Metrics
- **Average Max Return**: {avg_max_return:.2f}%
- **Average Max Drawdown**: {avg_max_drawdown:.2f}%
- **Average Current Return**: {avg_current_return:.2f}%
- **Average Holding Period**: {avg_holding_days:.1f} days

## Score Analysis
- **Score vs Return Correlation**: {score_corr_return:.3f}
- **Avg Score (Success)**: {avg_score_success:.1f}
- **Avg Score (Failure)**: {avg_score_failure:.1f}

## Performance by Index
"""
        
        for idx, row in index_stats.iterrows():
            summary += f"- **{idx}**: {row['ticker']:.0f} signals, {row['outcome']:.1f}% hit rate, {row['max_return_pct']:.2f}% avg max return\n"
        
        summary += """
                   ## Top 10 Best Performers
                   """
        top_performers = df.nlargest(10, 'max_return_pct')[['ticker', 'analysis_date', 'score', 'max_return_pct', 'outcome']]
        for _, row in top_performers.iterrows():
            summary += f"- **{row['ticker']}** ({row['analysis_date']}): Score {row['score']}, Max Return {row['max_return_pct']:.2f}%, {row['outcome']}\n"
        
        summary += """
                   ## Top 10 Worst Performers
                   """
        worst_performers = df.nsmallest(10, 'max_return_pct')[['ticker', 'analysis_date', 'score', 'max_return_pct', 'outcome']]
        for _, row in worst_performers.iterrows():
            summary += f"- **{row['ticker']}** ({row['analysis_date']}): Score {row['score']}, Max Return {row['max_return_pct']:.2f}%, {row['outcome']}\n"
        
        summary += f"\n---\n*Analysis completed at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return summary
    
    def run(self):
        """
        Execute the full backtest analysis pipeline.
        """
        logger.info("=" * 80)
        logger.info("Starting Backtest Analysis")
        logger.info("=" * 80)
        
        # Step 1: Scan reports directory
        reports = self.scan_reports_directory()
        
        if not reports:
            logger.error("No reports found to analyze")
            return
        
        # Step 2: Analyze all reports in parallel
        df = self.analyze_all_reports(reports)
        
        if df.empty:
            logger.error("No successful analyses")
            return
        
        # Step 3: Save CSV
        output_path = Path(self.output_csv)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(output_path, index=False)
        logger.info(f"Results saved to {output_path}")
        
        # Step 4: Generate and print summary
        summary = self.generate_summary(df)
        print("\n" + summary)
        
        # Save summary to file
        summary_path = output_path.parent / "backtest_summary.md"
        with open(summary_path, 'w') as f:
            f.write(summary)
        logger.info(f"Summary saved to {summary_path}")
        
        logger.info("=" * 80)
        logger.info("Backtest Analysis Complete")
        logger.info("=" * 80)


if __name__ == "__main__":
    analyzer = BacktestAnalyzer()
    analyzer.run()
