"""
Database Manager Module
=======================

SQLite database operations for storing and retrieving credit analysis data.
"""

import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages SQLite database operations for credit analysis data.

    Tables:
        - companies: Company information and basic financial data
        - financial_statements: Detailed financial statement data
        - cash_flows: UCA cash flow analysis results
        - ratios: Calculated financial ratios (DSCR, leverage, etc.)
    """

    def __init__(self, db_path: str):
        """
        Initialize database connection and create tables.

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

        self._create_tables()
        logger.info(f"Database initialized at: {self.db_path}")

    def _create_tables(self):
        """Create database tables if they don't exist."""

        # Companies table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ticker TEXT UNIQUE NOT NULL,
                company_name TEXT,
                source TEXT,
                last_updated TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Financial statements table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS financial_statements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                period_date TEXT NOT NULL,
                revenue REAL,
                operating_income REAL,
                ebitda REAL,
                depreciation_amortization REAL,
                interest_expense REAL,
                taxes REAL,
                net_income REAL,
                total_assets REAL,
                total_debt REAL,
                total_equity REAL,
                working_capital_change REAL,
                capex REAL,
                principal_payment REAL,
                metadata TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id),
                UNIQUE(company_id, period_date)
            )
        """)

        # Cash flows table (UCA analysis)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS cash_flows (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                analysis_date TEXT NOT NULL,
                operating_cash_flow REAL,
                free_cash_flow REAL,
                debt_service_requirement REAL,
                cash_available_for_debt REAL,
                noi REAL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # Ratios table
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS ratios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                ratio_name TEXT NOT NULL,
                ratio_value REAL,
                risk_level TEXT,
                threshold_healthy REAL,
                threshold_warning REAL,
                threshold_critical REAL,
                analysis_date TEXT NOT NULL,
                details TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        """)

        # Create indexes
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_companies_ticker ON companies(ticker)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_financial_statements_company
            ON financial_statements(company_id)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_cash_flows_company ON cash_flows(company_id)
        """)
        self.cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ratios_company ON ratios(company_id)
        """)

        self.conn.commit()

    def upsert_company(self, ticker: str, financial_data: Dict) -> int:
        """
        Insert or update company information.

        Args:
            ticker: Company ticker symbol
            financial_data: Dictionary containing financial data

        Returns:
            Company ID
        """
        now = datetime.now().isoformat()

        # Try to insert, update if exists
        self.cursor.execute("""
            INSERT INTO companies (ticker, company_name, source, last_updated, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(ticker) DO UPDATE SET
                company_name = excluded.company_name,
                source = excluded.source,
                last_updated = excluded.last_updated,
                updated_at = excluded.updated_at
        """, (
            ticker,
            financial_data.get("company_name", ticker),
            financial_data.get("source", "unknown"),
            financial_data.get("last_updated", now),
            now
        ))

        self.conn.commit()

        # Get company ID
        self.cursor.execute("SELECT id FROM companies WHERE ticker = ?", (ticker,))
        result = self.cursor.fetchone()

        company_id = result["id"]

        # Store financial statement
        self._store_financial_statement(company_id, financial_data)

        return company_id

    def _store_financial_statement(self, company_id: int, data: Dict):
        """Store detailed financial statement data."""
        period_date = datetime.now().strftime("%Y-%m-%d")

        metadata = {
            "avg_price": data.get("avg_price"),
            "price_volatility": data.get("price_volatility"),
            "avg_volume": data.get("avg_volume"),
            "data_points": data.get("data_points"),
            "simulation_date": data.get("simulation_date")
        }

        self.cursor.execute("""
            INSERT INTO financial_statements (
                company_id, period_date, revenue, operating_income, ebitda,
                depreciation_amortization, interest_expense, taxes, net_income,
                total_assets, total_debt, total_equity, working_capital_change,
                capex, principal_payment, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(company_id, period_date) DO UPDATE SET
                revenue = excluded.revenue,
                operating_income = excluded.operating_income,
                ebitda = excluded.ebitda,
                depreciation_amortization = excluded.depreciation_amortization,
                interest_expense = excluded.interest_expense,
                taxes = excluded.taxes,
                net_income = excluded.net_income,
                total_assets = excluded.total_assets,
                total_debt = excluded.total_debt,
                total_equity = excluded.total_equity,
                working_capital_change = excluded.working_capital_change,
                capex = excluded.capex,
                principal_payment = excluded.principal_payment,
                metadata = excluded.metadata
        """, (
            company_id,
            period_date,
            data.get("revenue"),
            data.get("operating_income"),
            data.get("ebitda"),
            data.get("depreciation_amortization"),
            data.get("interest_expense"),
            data.get("taxes"),
            data.get("net_income"),
            data.get("total_assets"),
            data.get("total_debt"),
            data.get("total_equity"),
            data.get("working_capital_change"),
            data.get("capex"),
            data.get("principal_payment"),
            json.dumps(metadata)
        ))

        self.conn.commit()

    def store_cash_flow(self, company_id: int, cash_flow: Dict):
        """
        Store UCA cash flow analysis results.

        Args:
            company_id: Company database ID
            cash_flow: Cash flow analysis results
        """
        analysis_date = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO cash_flows (
                company_id, analysis_date, operating_cash_flow, free_cash_flow,
                debt_service_requirement, cash_available_for_debt, noi, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            analysis_date,
            cash_flow.get("operating_cash_flow"),
            cash_flow.get("free_cash_flow"),
            cash_flow.get("debt_service_requirement"),
            cash_flow.get("cash_available_for_debt"),
            cash_flow.get("noi"),
            json.dumps(cash_flow.get("details", {}))
        ))

        self.conn.commit()

    def store_ratio(self, company_id: int, ratio_name: str, ratio_data: Dict):
        """
        Store calculated financial ratio.

        Args:
            company_id: Company database ID
            ratio_name: Name of the ratio (e.g., 'dscr', 'debt_to_equity')
            ratio_data: Ratio calculation results
        """
        analysis_date = datetime.now().isoformat()

        self.cursor.execute("""
            INSERT INTO ratios (
                company_id, ratio_name, ratio_value, risk_level,
                threshold_healthy, threshold_warning, threshold_critical,
                analysis_date, details
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            company_id,
            ratio_name,
            ratio_data.get("value"),
            ratio_data.get("risk_level"),
            ratio_data.get("threshold_healthy"),
            ratio_data.get("threshold_warning"),
            ratio_data.get("threshold_critical"),
            analysis_date,
            json.dumps(ratio_data.get("details", {}))
        ))

        self.conn.commit()

    def get_company(self, ticker: str) -> Optional[Dict]:
        """Get company information by ticker."""
        self.cursor.execute("""
            SELECT * FROM companies WHERE ticker = ?
        """, (ticker,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_all_companies(self) -> List[Dict]:
        """Get all companies."""
        self.cursor.execute("SELECT * FROM companies ORDER BY ticker")
        return [dict(row) for row in self.cursor.fetchall()]

    def get_latest_financial_statement(self, company_id: int) -> Optional[Dict]:
        """Get the most recent financial statement for a company."""
        self.cursor.execute("""
            SELECT * FROM financial_statements
            WHERE company_id = ?
            ORDER BY period_date DESC
            LIMIT 1
        """, (company_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_latest_cash_flow(self, company_id: int) -> Optional[Dict]:
        """Get the most recent cash flow analysis for a company."""
        self.cursor.execute("""
            SELECT * FROM cash_flows
            WHERE company_id = ?
            ORDER BY analysis_date DESC
            LIMIT 1
        """, (company_id,))

        row = self.cursor.fetchone()
        return dict(row) if row else None

    def get_latest_ratios(self, company_id: int) -> List[Dict]:
        """Get the most recent ratios for a company."""
        self.cursor.execute("""
            SELECT * FROM ratios
            WHERE company_id = ?
            AND analysis_date = (
                SELECT MAX(analysis_date) FROM ratios WHERE company_id = ?
            )
        """, (company_id, company_id))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_high_risk_companies(self, ratio_name: str = "dscr") -> List[Dict]:
        """Get companies with high risk ratings for a specific ratio."""
        self.cursor.execute("""
            SELECT c.ticker, c.company_name, r.ratio_value, r.risk_level, r.analysis_date
            FROM companies c
            JOIN ratios r ON c.id = r.company_id
            WHERE r.ratio_name = ? AND r.risk_level = 'HIGH'
            ORDER BY r.ratio_value ASC
        """, (ratio_name,))

        return [dict(row) for row in self.cursor.fetchall()]

    def get_analysis_summary(self) -> Dict:
        """Get summary statistics of the analysis."""
        summary = {}

        # Total companies
        self.cursor.execute("SELECT COUNT(*) as count FROM companies")
        summary["total_companies"] = self.cursor.fetchone()["count"]

        # DSCR statistics
        self.cursor.execute("""
            SELECT
                AVG(ratio_value) as avg_dscr,
                MIN(ratio_value) as min_dscr,
                MAX(ratio_value) as max_dscr,
                SUM(CASE WHEN risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk_count
            FROM ratios
            WHERE ratio_name = 'dscr'
        """)
        dscr_row = self.cursor.fetchone()
        summary["dscr"] = {
            "average": dscr_row["avg_dscr"],
            "min": dscr_row["min_dscr"],
            "max": dscr_row["max_dscr"],
            "high_risk_count": dscr_row["high_risk_count"]
        }

        return summary

    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
