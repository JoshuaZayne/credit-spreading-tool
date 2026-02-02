#!/usr/bin/env python3
"""
Credit Spreading Tool - Main Entry Point
=========================================

A comprehensive financial spreading template that automates UCA cash flow calculations,
DSCR computation, and leverage ratio analysis.

Usage:
    python src/main.py                           # Run full analysis
    python src/main.py --ticker AAPL             # Analyze specific ticker
    python src/main.py --export credit_report    # Export to Excel
    python src/main.py --list-tickers            # List available tickers
"""

import argparse
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data.data_loader import DataLoader
from src.data.database import DatabaseManager
from src.analysis.uca_cashflow import UCACashFlowAnalyzer
from src.analysis.dscr_calculator import DSCRCalculator
from src.analysis.leverage_ratios import LeverageRatioAnalyzer
from src.export.excel_exporter import ExcelExporter


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configure logging for the application."""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger("CreditSpreadingTool")


def load_config(config_path: str = None) -> dict:
    """Load configuration from JSON file."""
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config" / "config.json"

    with open(config_path, "r") as f:
        return json.load(f)


def run_analysis(
    config: dict,
    ticker: str = None,
    logger: logging.Logger = None
) -> dict:
    """
    Run the complete credit analysis pipeline.

    Args:
        config: Configuration dictionary
        ticker: Optional specific ticker to analyze
        logger: Logger instance

    Returns:
        Dictionary containing all analysis results
    """
    results = {
        "companies": [],
        "cash_flows": [],
        "dscr_results": [],
        "leverage_ratios": [],
        "summary": {}
    }

    # Initialize components
    data_loader = DataLoader(
        ticker_path=config["data_source"]["ticker_data_path"],
        excluded_files=config["data_source"]["excluded_files"]
    )

    db_path = Path(__file__).parent.parent / config["database"]["path"]
    db_manager = DatabaseManager(str(db_path))

    uca_analyzer = UCACashFlowAnalyzer(config["analysis"]["simulation"])
    dscr_calculator = DSCRCalculator(config["analysis"]["risk_thresholds"]["dscr"])
    leverage_analyzer = LeverageRatioAnalyzer(config["analysis"]["risk_thresholds"])

    # Load ticker data
    if ticker:
        tickers_data = data_loader.load_ticker(ticker)
        if tickers_data:
            tickers_data = {ticker: tickers_data}
        else:
            logger.error(f"Ticker {ticker} not found")
            return results
    else:
        tickers_data = data_loader.load_all_tickers()

    logger.info(f"Loaded {len(tickers_data)} tickers for analysis")

    # Process each ticker
    for ticker_symbol, ticker_data in tickers_data.items():
        logger.info(f"Analyzing {ticker_symbol}...")

        # Generate simulated financial data from OHLCV
        financial_data = data_loader.simulate_financials(ticker_symbol, ticker_data)

        if financial_data is None:
            logger.warning(f"Could not generate financial data for {ticker_symbol}")
            continue

        # Store company data
        company_id = db_manager.upsert_company(ticker_symbol, financial_data)
        results["companies"].append({
            "id": company_id,
            "ticker": ticker_symbol,
            "financial_data": financial_data
        })

        # UCA Cash Flow Analysis
        cash_flow = uca_analyzer.analyze(financial_data)
        db_manager.store_cash_flow(company_id, cash_flow)
        results["cash_flows"].append({
            "ticker": ticker_symbol,
            "cash_flow": cash_flow
        })

        # DSCR Calculation
        dscr_result = dscr_calculator.calculate(financial_data, cash_flow)
        db_manager.store_ratio(company_id, "dscr", dscr_result)
        results["dscr_results"].append({
            "ticker": ticker_symbol,
            "dscr": dscr_result
        })

        # Leverage Ratio Analysis
        leverage = leverage_analyzer.analyze(financial_data)
        for ratio_name, ratio_data in leverage.items():
            db_manager.store_ratio(company_id, ratio_name, ratio_data)
        results["leverage_ratios"].append({
            "ticker": ticker_symbol,
            "ratios": leverage
        })

    # Generate summary statistics
    results["summary"] = generate_summary(results, logger)

    # Close database connection
    db_manager.close()

    return results


def generate_summary(results: dict, logger: logging.Logger) -> dict:
    """Generate summary statistics from analysis results."""
    total_companies = len(results["companies"])

    if total_companies == 0:
        return {"error": "No companies analyzed"}

    # DSCR summary
    dscr_values = [r["dscr"]["value"] for r in results["dscr_results"] if r["dscr"]["value"] is not None]
    high_risk_dscr = sum(1 for r in results["dscr_results"] if r["dscr"]["risk_level"] == "HIGH")

    # Leverage summary
    high_leverage = sum(
        1 for r in results["leverage_ratios"]
        if any(ratio.get("risk_level") == "HIGH" for ratio in r["ratios"].values())
    )

    summary = {
        "total_companies": total_companies,
        "analysis_date": datetime.now().isoformat(),
        "dscr": {
            "average": sum(dscr_values) / len(dscr_values) if dscr_values else None,
            "min": min(dscr_values) if dscr_values else None,
            "max": max(dscr_values) if dscr_values else None,
            "high_risk_count": high_risk_dscr
        },
        "leverage": {
            "high_leverage_count": high_leverage
        },
        "risk_summary": {
            "healthy": total_companies - high_risk_dscr - high_leverage,
            "warning": 0,  # Would need more detailed tracking
            "high_risk": high_risk_dscr + high_leverage
        }
    }

    logger.info(f"Analysis complete. {total_companies} companies analyzed.")
    logger.info(f"High risk (DSCR < 1.25): {high_risk_dscr}")
    logger.info(f"High leverage concerns: {high_leverage}")

    return summary


def export_results(
    results: dict,
    config: dict,
    output_name: str,
    output_dir: str = None,
    logger: logging.Logger = None
) -> str:
    """Export analysis results to Excel."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / config["export"]["output_dir"]
    else:
        output_dir = Path(output_dir)

    output_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename with timestamp if configured
    if config["export"]["include_timestamp"]:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{output_name}_{timestamp}.xlsx"
    else:
        filename = f"{output_name}.xlsx"

    output_path = output_dir / filename

    exporter = ExcelExporter(config["analysis"]["risk_thresholds"])
    exporter.export(results, str(output_path))

    logger.info(f"Results exported to: {output_path}")
    return str(output_path)


def list_available_tickers(config: dict) -> list:
    """List all available tickers."""
    data_loader = DataLoader(
        ticker_path=config["data_source"]["ticker_data_path"],
        excluded_files=config["data_source"]["excluded_files"]
    )
    return data_loader.list_tickers()


def main():
    """Main entry point for the Credit Spreading Tool."""
    parser = argparse.ArgumentParser(
        description="Credit Spreading Tool - Automate UCA cash flow, DSCR, and leverage analysis"
    )
    parser.add_argument(
        "--ticker", "-t",
        help="Analyze specific ticker symbol"
    )
    parser.add_argument(
        "--export", "-e",
        help="Export results to Excel with specified name"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output directory for Excel export"
    )
    parser.add_argument(
        "--config", "-c",
        help="Path to configuration file"
    )
    parser.add_argument(
        "--list-tickers", "-l",
        action="store_true",
        help="List available tickers"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logging(log_level)

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        logger.error("Configuration file not found. Please ensure config/config.json exists.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid configuration file: {e}")
        sys.exit(1)

    # Handle --list-tickers
    if args.list_tickers:
        tickers = list_available_tickers(config)
        print("\nAvailable Tickers:")
        print("-" * 40)
        for ticker in sorted(tickers):
            print(f"  {ticker}")
        print(f"\nTotal: {len(tickers)} tickers")
        return

    # Run analysis
    logger.info("Starting Credit Spreading Tool analysis...")
    results = run_analysis(config, ticker=args.ticker, logger=logger)

    # Export if requested
    if args.export:
        export_results(
            results,
            config,
            args.export,
            output_dir=args.output,
            logger=logger
        )

    # Print summary
    if results["summary"]:
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Companies Analyzed: {results['summary'].get('total_companies', 0)}")
        print(f"Analysis Date: {results['summary'].get('analysis_date', 'N/A')}")

        if results["summary"].get("dscr"):
            dscr = results["summary"]["dscr"]
            print(f"\nDSCR Metrics:")
            print(f"  Average: {dscr.get('average', 'N/A'):.2f}" if dscr.get('average') else "  Average: N/A")
            print(f"  Range: {dscr.get('min', 'N/A'):.2f} - {dscr.get('max', 'N/A'):.2f}" if dscr.get('min') else "  Range: N/A")
            print(f"  High Risk Count: {dscr.get('high_risk_count', 0)}")

        print("=" * 60)


if __name__ == "__main__":
    main()
