"""
Data Loader Module
==================

Loads JSON ticker data and simulates financial metrics from OHLCV data.
"""

import json
import logging
import fnmatch
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

import numpy as np

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Loads financial data from JSON ticker files and simulates financial statements.

    The source data contains OHLCV (Open, High, Low, Close, Volume) market data.
    This class transforms that data into simulated financial metrics for credit analysis.
    """

    def __init__(self, ticker_path: str, excluded_files: List[str] = None):
        """
        Initialize the DataLoader.

        Args:
            ticker_path: Path to directory containing JSON ticker files
            excluded_files: List of file patterns to exclude (supports wildcards)
        """
        self.ticker_path = Path(ticker_path)
        self.excluded_files = excluded_files or []

        if not self.ticker_path.exists():
            logger.warning(f"Ticker data path does not exist: {ticker_path}")

    def _is_excluded(self, filename: str) -> bool:
        """Check if a filename matches any exclusion pattern."""
        for pattern in self.excluded_files:
            if fnmatch.fnmatch(filename, pattern):
                return True
        return False

    def list_tickers(self) -> List[str]:
        """
        List all available ticker symbols.

        Returns:
            List of ticker symbols (without .json extension)
        """
        if not self.ticker_path.exists():
            return []

        tickers = []
        for file_path in self.ticker_path.glob("*.json"):
            if not self._is_excluded(file_path.name):
                ticker = file_path.stem
                tickers.append(ticker)

        return sorted(tickers)

    def load_ticker(self, ticker: str) -> Optional[Dict]:
        """
        Load data for a specific ticker.

        Args:
            ticker: Ticker symbol to load

        Returns:
            Dictionary containing ticker data, or None if not found
        """
        file_path = self.ticker_path / f"{ticker}.json"

        if not file_path.exists():
            logger.error(f"Ticker file not found: {file_path}")
            return None

        if self._is_excluded(file_path.name):
            logger.warning(f"Ticker {ticker} is in exclusion list")
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            return data
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing JSON for {ticker}: {e}")
            return None
        except Exception as e:
            logger.error(f"Error loading ticker {ticker}: {e}")
            return None

    def load_all_tickers(self, max_tickers: int = None) -> Dict[str, Dict]:
        """
        Load all available ticker data.

        Args:
            max_tickers: Maximum number of tickers to load (for testing)

        Returns:
            Dictionary mapping ticker symbols to their data
        """
        all_data = {}
        tickers = self.list_tickers()

        if max_tickers:
            tickers = tickers[:max_tickers]

        for ticker in tickers:
            data = self.load_ticker(ticker)
            if data:
                all_data[ticker] = data

        logger.info(f"Loaded {len(all_data)} tickers")
        return all_data

    def _extract_ohlcv_stats(self, data: Dict) -> Dict[str, Any]:
        """
        Extract aggregate statistics from OHLCV data.

        Args:
            data: Raw ticker data with OHLCV information

        Returns:
            Dictionary with aggregated price/volume statistics
        """
        stats = {
            "avg_price": 0,
            "avg_volume": 0,
            "total_volume": 0,
            "price_volatility": 0,
            "data_points": 0,
            "latest_price": 0,
            "highest_price": 0,
            "lowest_price": float("inf")
        }

        prices = []
        volumes = []

        # Process data structure (handles nested time periods)
        if "data" in data:
            for timeframe, dates in data["data"].items():
                if isinstance(dates, dict):
                    for date, times in dates.items():
                        if isinstance(times, dict):
                            for time, ohlcv in times.items():
                                if isinstance(ohlcv, dict):
                                    if "close" in ohlcv:
                                        prices.append(ohlcv["close"])
                                    if "volume" in ohlcv:
                                        volumes.append(ohlcv["volume"])
                                    if "high" in ohlcv:
                                        stats["highest_price"] = max(
                                            stats["highest_price"],
                                            ohlcv["high"]
                                        )
                                    if "low" in ohlcv and ohlcv["low"] > 0:
                                        stats["lowest_price"] = min(
                                            stats["lowest_price"],
                                            ohlcv["low"]
                                        )

        if prices:
            stats["avg_price"] = np.mean(prices)
            stats["latest_price"] = prices[-1] if prices else 0
            stats["price_volatility"] = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
            stats["data_points"] = len(prices)

        if volumes:
            stats["avg_volume"] = np.mean(volumes)
            stats["total_volume"] = sum(volumes)

        if stats["lowest_price"] == float("inf"):
            stats["lowest_price"] = 0

        return stats

    def simulate_financials(self, ticker: str, data: Dict) -> Optional[Dict[str, Any]]:
        """
        Simulate financial statements from OHLCV market data.

        This transforms price/volume data into simulated financial metrics
        for demonstration purposes in credit analysis.

        Args:
            ticker: Ticker symbol
            data: Raw ticker data

        Returns:
            Dictionary containing simulated financial metrics
        """
        try:
            # Extract market statistics
            ohlcv_stats = self._extract_ohlcv_stats(data)

            if ohlcv_stats["data_points"] == 0:
                logger.warning(f"No data points found for {ticker}")
                return None

            # Get metadata
            metadata = data.get("metadata", {})

            # Simulation parameters (realistic ratios)
            # Using price * volume as a proxy for market cap / revenue proxy
            market_proxy = ohlcv_stats["avg_price"] * ohlcv_stats["avg_volume"]

            # Scale to reasonable financial statement values
            # Higher price volatility suggests higher business risk
            risk_factor = 1 + ohlcv_stats["price_volatility"]

            # Simulate revenue (scaled by market proxy)
            revenue = max(market_proxy * 1000, 1_000_000)  # Minimum $1M revenue

            # Operating metrics
            operating_margin = 0.15 / risk_factor  # Lower margin for volatile stocks
            ebitda_margin = 0.20 / risk_factor

            operating_income = revenue * operating_margin
            ebitda = revenue * ebitda_margin

            # Depreciation and Amortization
            depreciation = revenue * 0.03

            # Interest and taxes
            debt = revenue * 0.40 * risk_factor  # More volatile = more debt assumption
            interest_expense = debt * 0.05
            tax_rate = 0.25
            ebt = operating_income - interest_expense
            taxes = max(ebt * tax_rate, 0)
            net_income = ebt - taxes

            # Working capital changes
            working_capital_change = revenue * 0.02 * (1 if np.random.random() > 0.5 else -1)

            # Capital expenditures
            capex = revenue * 0.05

            # Equity (derived from assets and debt)
            total_assets = revenue * 1.2
            total_equity = total_assets - debt

            # Principal payment (assuming 10-year amortization)
            principal_payment = debt * 0.10

            financial_data = {
                "ticker": ticker,
                "company_name": metadata.get("ticker", ticker),
                "last_updated": metadata.get("last_updated", datetime.now().isoformat()),
                "source": metadata.get("source", "simulated"),

                # Income Statement
                "revenue": round(revenue, 2),
                "operating_income": round(operating_income, 2),
                "ebitda": round(ebitda, 2),
                "depreciation_amortization": round(depreciation, 2),
                "interest_expense": round(interest_expense, 2),
                "taxes": round(taxes, 2),
                "net_income": round(net_income, 2),

                # Balance Sheet
                "total_assets": round(total_assets, 2),
                "total_debt": round(debt, 2),
                "total_equity": round(total_equity, 2),

                # Cash Flow Components
                "working_capital_change": round(working_capital_change, 2),
                "capex": round(capex, 2),
                "principal_payment": round(principal_payment, 2),

                # Market Data
                "avg_price": round(ohlcv_stats["avg_price"], 2),
                "price_volatility": round(ohlcv_stats["price_volatility"], 4),
                "avg_volume": round(ohlcv_stats["avg_volume"], 0),

                # Metadata
                "data_points": ohlcv_stats["data_points"],
                "simulation_date": datetime.now().isoformat()
            }

            return financial_data

        except Exception as e:
            logger.error(f"Error simulating financials for {ticker}: {e}")
            return None
