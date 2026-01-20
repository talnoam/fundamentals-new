import logging
import yaml
import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor, as_completed # for performance

# Add the parent directory to the Python path so we can import from src
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

# import the internal modules (assuming they are in the src directory)
# note: these are placeholders until we write them
from src.ticker_provider import TickerProvider
from src.data_loader import DataEngine
from src.filters import FilterEngine
from src.detector import PatternDetector
from src.scorer import ScoringEngine
from src.visualizer import Visualizer

# define the professional logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scanner.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StockScanner")

# External helper function for parallel processing
def analyze_single_ticker(ticker: str, data_engine, detector, scorer):
    """
    Runs the entire analysis for a single ticker. This function runs in a separate Process.
    """
    try:
        df = data_engine.fetch_historical_data(ticker)
        if df is None or df.empty:
            return None

        pattern_result = detector.analyze_convergence(df)
        
        # Only if there is a breakout (1-2 days above the line) and high quality, we calculate the score
        if pattern_result.get('is_breaking_out') and pattern_result.get('r2_high', 0) >= 0.5:
            score = scorer.calculate_score(df, pattern_result)
            if score > 0:
                return {
                    'ticker': ticker,
                    'data': df,
                    'pattern': pattern_result,
                    'score': score
                }
    except Exception:
        # In Multiprocessing, it is important to catch errors so that the Pool does not crash
        return None
    return None

class StockScanner:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        self.data_engine = DataEngine(self.config.get('data', {}))
        # Pass data_engine to FilterEngine so it can use cached data
        self.filter_engine = FilterEngine(self.config.get('filters', {}), data_engine=self.data_engine)
        self.detector = PatternDetector(self.config.get('patterns', {}))
        self.scorer = ScoringEngine(self.config.get('scoring', {}))
        self.visualizer = Visualizer(self.config.get('visualization', {}))

    def _load_config(self, path: str) -> Dict:
        try:
            with open(path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning(f"Config file not found at {path}. Using defaults.")
            return {}

    def scan(self, ticker_list: List[str]):
        """
        the main process of the scan
        """
        logger.info(f"Starting scan for {len(ticker_list)} tickers...")

        # step 1: fetch the fundamental data and primary filtering (Market Cap, etc.)
        # done in a vectorized or fast way
        raw_candidates = self.filter_engine.apply_coarse_filters(ticker_list)
        logger.info(f"After coarse filtering: {len(raw_candidates)} candidates remain.")

        # step 2: graph analysis (the computationally heavy part)
        # here we use Parallel Processing in the ProcessPoolExecutor
        final_candidates = []

        max_workers = self.config.get('performance', {}).get('max_workers', 8)

        logger.info(f"Spawning Pool with {max_workers} workers...")
        
        with ProcessPoolExecutor(max_workers=max_workers) as executor:
            # Sending all the tasks to the Pool
            futures = {
                executor.submit(analyze_single_ticker, ticker, self.data_engine, self.detector, self.scorer): ticker 
                for ticker in raw_candidates
            }
            
            for future in as_completed(futures):
                result = future.result()
                if result:
                    final_candidates.append(result)
                    logger.info(f"✅ Found valid pattern for {result['ticker']} (Score: {result['score']:.2f})")

        # Sorting by the weighted score (highest first)
        final_candidates.sort(key=lambda x: x['score'], reverse=True)

        # step 4: output and visualization
        self._generate_outputs(final_candidates)

    def _generate_outputs(self, candidates: List[Dict]):
        if not candidates:
            logger.info("No breakout candidates found today.")
            return

        logger.info(f"Scan complete. Found {len(candidates)} candidates.")
        
        # create the charts in Plotly for the Top N
        top_n = self.config.get('visualization', {}).get('top_n', 5)
        for candidate in candidates[:top_n]:
            self.visualizer.create_chart(
                candidate['ticker'], 
                candidate['data'], 
                candidate['pattern'],
                candidate['score']
            )

if __name__ == "__main__":
    # initialize the scanner
    scanner = StockScanner()

    # initialize the ticker provider
    provider = TickerProvider(cache_expiry_days=1)

    # fetch all the tickers (S&P 500, Dow, Nasdaq)
    tickers_to_scan = provider.get_all_tickers(include_nasdaq=True, include_sp500=True, include_dow=True)
    
    scanner.scan(tickers_to_scan)