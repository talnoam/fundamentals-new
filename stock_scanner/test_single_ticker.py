#!/usr/bin/env python3
"""
Script to test and examine pattern detection and scoring for a single ticker.
Uses analyze_single_ticker and create_chart to visualize the results.
"""

import logging
import yaml
import sys
import argparse
from pathlib import Path

# Add the parent directory to the Python path so we can import from src
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from src.data_loader import DataEngine
from src.detector import PatternDetector
from src.scorer import ScoringEngine
from src.visualizer import Visualizer
from stock_scanner.scanner import analyze_single_ticker

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TickerTester")

# Define the ticker to analyze here
TICKER = "BLK"  # Change this to test different tickers


def load_config(config_path: str = "config/settings.yaml"):
    """Load configuration from YAML file."""
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Config file not found at {config_path}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Test pattern detection and scoring for a single ticker"
    )
    parser.add_argument(
        "--ticker",
        type=str,
        default=TICKER,
        help=f"Stock ticker symbol to analyze (default: {TICKER})"
    )
    parser.add_argument(
        "--config",
        type=str,
        default="config/settings.yaml",
        help="Path to configuration file (default: config/settings.yaml)"
    )
    
    args = parser.parse_args()
    ticker = args.ticker.upper()
    
    logger.info(f"Testing pattern detection and scoring for {ticker}")
    
    # Load configuration
    config = load_config(args.config)
    
    # Initialize components
    logger.info("Initializing components...")
    data_engine = DataEngine(config.get('data', {}))
    detector = PatternDetector(config.get('patterns', {}))
    scorer = ScoringEngine(config.get('scoring', {}))
    visualizer = Visualizer(config.get('visualization', {}))
    
    # Analyze the ticker
    logger.info(f"Analyzing {ticker}...")
    result = analyze_single_ticker(ticker, data_engine, detector, scorer)
    
    if result is None:
        logger.warning(f"No valid pattern found for {ticker}. This could mean:")
        logger.warning("  - No breakout detected")
        logger.warning("  - R² quality below threshold (< 0.5)")
        logger.warning("  - Score was 0 or negative")
        logger.warning("  - Data fetch failed")
        return
    
    # Display results
    logger.info(f"✅ Pattern detected for {ticker}!")
    logger.info(f"   Score: {result['score']:.2f}/100")
    logger.info(f"   Compression: {result['pattern'].get('compression', 0):.2f}")
    logger.info(f"   R² High: {result['pattern'].get('r2_high', 0):.2f}")
    logger.info(f"   Is Breaking Out: {result['pattern'].get('is_breaking_out', False)}")
    logger.info(f"   Breakout Age: {result['pattern'].get('breakout_age', 'N/A')} days")
    
    # Create chart
    logger.info(f"Generating chart for {ticker}...")
    visualizer.create_chart(
        result['ticker'],
        result['data'],
        result['pattern'],
        result['score']
    )
    
    logger.info(f"Analysis complete! Chart saved to {visualizer.charts_output_dir}")


if __name__ == "__main__":
    main()
