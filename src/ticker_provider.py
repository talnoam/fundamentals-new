import requests
import pandas as pd
import logging
import os
from io import StringIO
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TickerProvider:
    def __init__(self, cache_dir: str = ".cache", cache_expiry_days: int = 1):
        self.cache_dir = cache_dir
        self.cache_expiry_days = cache_expiry_days
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def _get_cache_path(self, name: str) -> str:
        return os.path.join(self.cache_dir, f"{name}_tickers.csv")

    def _is_cache_valid(self, path: str) -> bool:
        if not os.path.exists(path):
            return False
        file_age = datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))
        return file_age < timedelta(days=self.cache_expiry_days)

    def get_all_tickers(self, include_nasdaq=True, include_sp500=True, include_dow=True) -> list:
        """
        unified function that fetches all the tickers without duplicates
        """
        all_tickers = set()
        
        if include_sp500:
            sp500_tickers = self._fetch_with_cache("sp500", self._fetch_sp500)
            if sp500_tickers:
                all_tickers.update(sp500_tickers)
        if include_dow:
            dow_tickers = self._fetch_with_cache("dow", self._fetch_dow)
            if dow_tickers:
                all_tickers.update(dow_tickers)
        if include_nasdaq:
            nasdaq_tickers = self._fetch_with_cache("nasdaq", self._fetch_nasdaq)
            if nasdaq_tickers:
                all_tickers.update(nasdaq_tickers)
            
        logger.info(f"Total unique tickers collected: {len(all_tickers)}")
        return sorted(list(all_tickers))

    def _fetch_sp500(self):
        try:
            url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()

            tables = pd.read_html(StringIO(resp.text))
            if not tables:
                raise ValueError("No tables found on Wikipedia S&P 500 page.")

            df = tables[0]
            if "Symbol" not in df.columns:
                raise KeyError(f"Column 'Symbol' missing. Found: {df.columns.tolist()}")

            return df["Symbol"].str.replace(".", "-", regex=False).tolist()

        except requests.exceptions.RequestException as e:
            logger.error(f"Network error fetching S&P 500: {e}")
        except Exception as e:
            logger.error(f"Unexpected error parsing S&P 500: {e}")
        
        return [] # Fallback to an empty list so the pipeline can continue

    def _fetch_dow(self):
        try:
            url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()

            tables = pd.read_html(StringIO(resp.text))

            # search for a table that contains symbols - more resilient to changes in table position
            for i, tbl in enumerate(tables):
                cols = [str(c) for c in tbl.columns]
                symbol_col = next((c for c in cols if "Symbol" in c or "Ticker" in c), None)
                if symbol_col:
                    return tbl[symbol_col].astype(str).str.strip().str.replace(".", "-", regex=False).tolist()
            
            raise ValueError("Could not identify Dow Jones components table.")
        
        except Exception as e:
            logger.error(f"Error fetching Dow Jones: {e}")
            return []

    def _fetch_nasdaq(self):
        try:
            url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()

            df = pd.read_csv(StringIO(resp.text), sep="|", on_bad_lines='skip')

            if "Symbol" not in df.columns:
                logger.error("Nasdaq file format changed - 'Symbol' column not found.")
                return []
            
            # clean data: remove the footer row of Nasdaq
            df = df[df["Symbol"].notna()]
            df = df[~df["Symbol"].str.contains("File Creation Time", na=False)]
            
            if "Test Issue" in df.columns:
                df = df[df["Test Issue"] == "N"]

            return df["Symbol"].astype(str).str.strip().str.replace(".", "-", regex=False).unique().tolist()

        except Exception as e:
            logger.error(f"Error fetching Nasdaq tickers: {e}")
            return []

    def _fetch_with_cache(self, name: str, fetch_func) -> list:
        """
        general cache manager that uses Try-Catch
        """
        cache_path = self._get_cache_path(name)
        
        # 1. try to load from cache if it's valid
        if self._is_cache_valid(cache_path):
            try:
                cached_data = pd.read_csv(cache_path)['Symbol'].tolist()
                if cached_data:
                    logger.info(f"Loaded {len(cached_data)} {name} tickers from cache.")
                    return cached_data
            except Exception as e:
                logger.warning(f"Failed to read cache for {name}: {e}")

        # 2. try to fetch from source
        tickers = fetch_func()
        
        if tickers:
            try:
                pd.DataFrame({'Symbol': tickers}).to_csv(cache_path, index=False)
                logger.info(f"Successfully cached {len(tickers)} {name} tickers.")
                return tickers
            except Exception as e:
                logger.warning(f"Failed to write cache for {name}: {e}")
                return tickers
        
        # 3. fallback: if everything fails, try to load expired cache
        if os.path.exists(cache_path):
            logger.warning(f"Source failed for {name}. Falling back to expired cache.")
            return pd.read_csv(cache_path)['Symbol'].tolist()
            
        return []