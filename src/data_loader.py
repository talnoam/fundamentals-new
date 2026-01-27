import yfinance as yf
import pandas as pd
import os
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class DataEngine:
    def __init__(self, config: dict):
        self.cache_dir = config.get('cache_dir', '.cache/historical_data')
        self.cache_expiry_hours = config.get('cache_expiry_hours', 12)
        self.default_period = config.get('default_period', '1y')
        self.default_interval = config.get('default_interval', '1d')
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def fetch_historical_data(self, ticker: str, force_refresh: bool = False) -> pd.DataFrame:
        """
        Fetches historical data (Open, High, Low, Close, Volume). 
        First checks the local cache.
        """
        cache_path = os.path.join(self.cache_dir, f"{ticker}.parquet")
        
        # Checking whether the information exists and is valid
        if not force_refresh and self._is_cache_valid(cache_path):
            try:
                df = pd.read_parquet(cache_path)
                if not df.empty:
                    return df
            except Exception as e:
                logger.warning(f"Could not read cache for {ticker}: {e}")

        # If there is no cache or it has expired — fetch from the API.
        try:
            logger.info(f"Downloading data for {ticker}...")
            # We use auto_adjust=True to get prices adjusted for dividends and splits.
            df = yf.download(
                ticker, 
                period=self.default_period, 
                interval=self.default_interval,
                progress=False,
                auto_adjust=True 
            )

            if df.empty:
                logger.warning(f"No data returned for {ticker}")
                return pd.DataFrame()

            # Clean up column structure
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Handle duplicate columns (Yahoo Finance API bug)
            if df.columns.duplicated().any():
                logger.warning(f"{ticker}: Duplicate columns detected, keeping first occurrence")
                df = df.loc[:, ~df.columns.duplicated(keep='first')]
            
            # Select required columns
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()

            # Saving to the cache.
            df.to_parquet(cache_path)
            
            return df

        except Exception as e:
            logger.error(f"Error fetching {ticker} from Yahoo Finance: {e}")
            return pd.DataFrame()

    def fetch_historical_data_range(self, ticker: str, start_date: datetime, end_date: datetime = None) -> pd.DataFrame:
        """
        Fetches historical data for a specific date range.
        Optimized for backtesting - fetches from start_date to end_date (or today).
        
        Args:
            ticker: Stock ticker symbol
            start_date: Start date for data fetch
            end_date: End date for data fetch (defaults to today)
            
        Returns:
            DataFrame with OHLCV data
        """
        if end_date is None:
            end_date = datetime.now()
        
        # Create a cache key based on date range
        cache_filename = f"{ticker}_range_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
        cache_path = os.path.join(self.cache_dir, cache_filename)
        
        # Check cache (valid for 1 day for date ranges)
        if self._is_range_cache_valid(cache_path, end_date):
            try:
                df = pd.read_parquet(cache_path)
                if not df.empty:
                    logger.debug(f"{ticker}: Loaded from range cache")
                    return df
            except Exception as e:
                logger.warning(f"Could not read range cache for {ticker}: {e}")
        
        # Fetch from API with date range
        try:
            logger.info(f"Downloading {ticker} from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...")
            df = yf.download(
                ticker,
                start=start_date.strftime('%Y-%m-%d'),
                end=end_date.strftime('%Y-%m-%d'),
                interval=self.default_interval,
                progress=False,
                auto_adjust=True
            )
            
            if df.empty:
                logger.warning(f"{ticker}: No data returned for date range")
                return pd.DataFrame()
            
            # Clean up column structure
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            
            # Handle duplicate columns (Yahoo Finance API bug)
            if df.columns.duplicated().any():
                logger.warning(f"{ticker}: Duplicate columns detected, keeping first occurrence")
                df = df.loc[:, ~df.columns.duplicated(keep='first')]
            
            # Select required columns
            df = df[['Open', 'High', 'Low', 'Close', 'Volume']].dropna()
            
            # Save to cache
            df.to_parquet(cache_path)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {ticker} date range from Yahoo Finance: {e}")
            return pd.DataFrame()

    def _is_range_cache_valid(self, path: str, end_date: datetime) -> bool:
        """Check if range cache is valid. Only valid if end_date is not today."""
        if not os.path.exists(path):
            return False
        
        # If end_date is today or recent, cache expires quickly (1 hour)
        days_old = (datetime.now() - end_date).days
        if days_old <= 1:
            file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
            return file_age < timedelta(hours=1)
        
        # For historical data, cache is valid for longer (24 hours)
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        return file_age < timedelta(hours=24)

    def _is_cache_valid(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        return file_age < timedelta(hours=self.cache_expiry_hours)

    def bulk_fetch(self, tickers: list):
        """
        Optimization for downloading data for many stocks in parallel.
        """
        # In Yahoo Finance it's recommended to download in batches so as not to get blocked.
        logger.info(f"Bulk fetching {len(tickers)} tickers...")
        data = yf.download(tickers, period=self.default_period, interval=self.default_interval, group_by='ticker', progress=True)
        
        for ticker in tickers:
            try:
                ticker_df = data[ticker].dropna()
                if not ticker_df.empty:
                    cache_path = os.path.join(self.cache_dir, f"{ticker}.parquet")
                    ticker_df.to_parquet(cache_path)
            except KeyError:
                continue