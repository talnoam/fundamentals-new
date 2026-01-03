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
            all_tickers.update(self._fetch_with_cache("sp500", self._fetch_sp500))
        if include_dow:
            all_tickers.update(self._fetch_with_cache("dow", self._fetch_dow))
        if include_nasdaq:
            all_tickers.update(self._fetch_with_cache("nasdaq", self._fetch_nasdaq))
            
        logger.info(f"Total unique tickers collected: {len(all_tickers)}")
        return sorted(list(all_tickers))

    def _fetch_with_cache(self, name: str, fetch_func) -> list:
        cache_path = self._get_cache_path(name)
        
        if self._is_cache_valid(cache_path):
            logger.info(f"Loading {name} tickers from cache.")
            return pd.read_csv(cache_path)['Symbol'].tolist()
        
        try:
            logger.info(f"Fetching {name} tickers from source...")
            tickers = fetch_func()
            pd.DataFrame({'Symbol': tickers}).to_csv(cache_path, index=False)
            return tickers
        except Exception as e:
            logger.error(f"Failed to fetch {name} tickers: {e}")
            return pd.read_csv(cache_path)['Symbol'].tolist() if os.path.exists(cache_path) else []

    def _fetch_sp500(self):
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text))
        return tables[0]["Symbol"].str.replace(".", "-", regex=False).tolist()

    def _fetch_dow(self):
        url = "https://en.wikipedia.org/wiki/Dow_Jones_Industrial_Average"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text))
        
        df = next(tbl for tbl in tables if "Symbol" in tbl.columns or "Ticker symbol" in tbl.columns)
        col = "Symbol" if "Symbol" in df.columns else "Ticker symbol"
        return df[col].astype(str).str.strip().str.replace(".", "-", regex=False).tolist()

    def _fetch_nasdaq(self):
        url = "https://www.nasdaqtrader.com/dynamic/symdir/nasdaqlisted.txt"
        resp = requests.get(url, headers=self.headers)
        resp.raise_for_status()
        df = pd.read_csv(StringIO(resp.text), sep="|")
        if "Test Issue" in df.columns:
            df = df[df["Test Issue"] == "N"]
        return df["Symbol"].dropna().astype(str).str.strip().str.replace(".", "-", regex=False).unique().tolist()