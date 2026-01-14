import logging
import yaml
import pandas as pd
import sys
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ProcessPoolExecutor # for performance

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

class StockScanner:
    def __init__(self, config_path: str = "config/settings.yaml"):
        self.config = self._load_config(config_path)
        
        # initialize the different engines
        self.data_engine = DataEngine(self.config.get('data', {}))
        self.filter_engine = FilterEngine(self.config.get('filters', {}))
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
        
        for ticker in raw_candidates:
            try:
                # fetch the historical data (OHLCV)
                df = self.data_engine.fetch_historical_data(ticker)
                
                if df is None or df.empty:
                    continue

                # detect convergence
                pattern_result = self.detector.analyze_convergence(df)
                
                if pattern_result['is_converging']:
                    # score
                    score = self.scorer.calculate_score(df, pattern_result)
                    
                    final_candidates.append({
                        'ticker': ticker,
                        'data': df,
                        'pattern': pattern_result,
                        'score': score
                    })
                    logger.info(f"Found valid pattern for {ticker} (Score: {score:.2f})")
            
            except Exception as e:
                logger.error(f"Error analyzing {ticker}: {str(e)}")

        # step 3: sorting by score
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