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

            # Saving to the cache.
            df.to_parquet(cache_path)
            return df

        except Exception as e:
            logger.error(f"Error fetching {ticker} from Yahoo Finance: {e}")
            return pd.DataFrame()

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