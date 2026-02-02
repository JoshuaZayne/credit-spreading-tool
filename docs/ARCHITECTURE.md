# Credit Spreading Tool - Architecture Documentation

## Overview

The Credit Spreading Tool is a comprehensive financial analysis application designed to automate credit analysis workflows. It processes financial data to calculate UCA (Uniform Credit Analysis) cash flows, DSCR (Debt Service Coverage Ratio), and leverage ratios, storing results in a SQLite database and exporting to formatted Excel workbooks.

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Credit Spreading Tool                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │  Data Layer  │───>│Analysis Layer│───>│ Export Layer │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│         │                   │                   │                 │
│         v                   v                   v                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐       │
│  │ JSON Ticker  │    │   SQLite     │    │    Excel     │       │
│  │    Files     │    │   Database   │    │  Workbooks   │       │
│  └──────────────┘    └──────────────┘    └──────────────┘       │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### 1. Data Layer (`src/data/`)

#### DataLoader (`data_loader.py`)
- **Purpose**: Load and transform ticker data from JSON files
- **Key Features**:
  - Pattern-based file filtering
  - OHLCV data aggregation
  - Financial metric simulation from market data

```python
class DataLoader:
    def load_ticker(ticker: str) -> Optional[Dict]
    def load_all_tickers(max_tickers: int = None) -> Dict[str, Dict]
    def simulate_financials(ticker: str, data: Dict) -> Optional[Dict]
```

#### DatabaseManager (`database.py`)
- **Purpose**: SQLite database operations for persistent storage
- **Tables**:
  - `companies`: Company metadata
  - `financial_statements`: Financial statement data
  - `cash_flows`: UCA cash flow analysis results
  - `ratios`: Calculated financial ratios

```python
class DatabaseManager:
    def upsert_company(ticker: str, financial_data: Dict) -> int
    def store_cash_flow(company_id: int, cash_flow: Dict)
    def store_ratio(company_id: int, ratio_name: str, ratio_data: Dict)
    def get_analysis_summary() -> Dict
```

### 2. Analysis Layer (`src/analysis/`)

#### UCACashFlowAnalyzer (`uca_cashflow.py`)
- **Purpose**: Uniform Credit Analysis cash flow calculations
- **Calculations**:
  - Operating Cash Flow = Net Income + D&A - Working Capital Change
  - Free Cash Flow = Operating Cash Flow - CapEx
  - Debt Service Coverage from operations

```python
class UCACashFlowAnalyzer:
    def analyze(financial_data: Dict) -> Dict
    def calculate_sources_and_uses(financial_data: Dict) -> Dict
    def assess_cash_flow_quality(uca_result: Dict) -> Dict
```

#### DSCRCalculator (`dscr_calculator.py`)
- **Purpose**: Debt Service Coverage Ratio calculations
- **Formula**: DSCR = Net Operating Income / Total Debt Service
- **Risk Thresholds**:
  - Healthy: >= 1.50
  - Warning: 1.25 - 1.50
  - High Risk: < 1.25

```python
class DSCRCalculator:
    def calculate(financial_data: Dict, cash_flow_data: Dict = None) -> Dict
    def sensitivity_analysis(noi: float, total_debt_service: float) -> Dict
```

#### LeverageRatioAnalyzer (`leverage_ratios.py`)
- **Purpose**: Comprehensive leverage analysis
- **Ratios**:
  - Debt-to-Equity: Total Debt / Total Equity
  - Debt-to-EBITDA: Total Debt / EBITDA
  - Interest Coverage: EBITDA / Interest Expense

```python
class LeverageRatioAnalyzer:
    def analyze(financial_data: Dict) -> Dict
    def calculate_debt_to_equity(financial_data: Dict) -> Dict
    def calculate_debt_to_ebitda(financial_data: Dict) -> Dict
    def calculate_interest_coverage(financial_data: Dict) -> Dict
```

### 3. Export Layer (`src/export/`)

#### ExcelExporter (`excel_exporter.py`)
- **Purpose**: Generate formatted Excel reports
- **Worksheets**:
  - Summary: Overview with key metrics
  - UCA Cash Flow: Detailed cash flow analysis
  - DSCR Analysis: Debt service coverage with risk flags
  - Leverage Ratios: All leverage metrics with formatting

```python
class ExcelExporter:
    def export(results: Dict, output_path: str) -> str
```

## Data Flow

```
1. Input Processing
   ┌──────────────────┐
   │  JSON Ticker     │
   │  Files (OHLCV)   │
   └────────┬─────────┘
            │
            v
2. Data Transformation
   ┌──────────────────┐
   │  DataLoader      │
   │  - Load files    │
   │  - Extract stats │
   │  - Simulate      │
   │    financials    │
   └────────┬─────────┘
            │
            v
3. Storage
   ┌──────────────────┐
   │  SQLite Database │
   │  - Companies     │
   │  - Financials    │
   └────────┬─────────┘
            │
            v
4. Analysis
   ┌──────────────────┐
   │  Analysis Layer  │
   │  - UCA Cash Flow │
   │  - DSCR          │
   │  - Leverage      │
   └────────┬─────────┘
            │
            v
5. Output
   ┌──────────────────┐
   │  Excel Export    │
   │  - Formatted     │
   │  - Color-coded   │
   │  - Multi-sheet   │
   └──────────────────┘
```

## Database Schema

```sql
-- Companies table
CREATE TABLE companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker TEXT UNIQUE NOT NULL,
    company_name TEXT,
    source TEXT,
    last_updated TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Financial statements table
CREATE TABLE financial_statements (
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
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Cash flows table (UCA analysis)
CREATE TABLE cash_flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    company_id INTEGER NOT NULL,
    analysis_date TEXT NOT NULL,
    operating_cash_flow REAL,
    free_cash_flow REAL,
    debt_service_requirement REAL,
    cash_available_for_debt REAL,
    noi REAL,
    details TEXT,
    FOREIGN KEY (company_id) REFERENCES companies(id)
);

-- Ratios table
CREATE TABLE ratios (
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
    FOREIGN KEY (company_id) REFERENCES companies(id)
);
```

## Configuration

The application is configured via `config/config.json`:

```json
{
    "data_source": {
        "ticker_data_path": "path/to/ticker/files",
        "file_pattern": "*.json",
        "excluded_files": ["MASTER.json", "TEST_*.json"]
    },
    "database": {
        "path": "data/credit_analysis.db"
    },
    "analysis": {
        "simulation": {
            "revenue_multiplier": 1000000,
            "operating_margin": 0.15,
            "ebitda_margin": 0.20
        },
        "risk_thresholds": {
            "dscr": {"healthy": 1.5, "warning": 1.25, "critical": 1.0},
            "debt_to_equity": {"healthy": 1.0, "warning": 2.0, "critical": 3.0}
        }
    }
}
```

## Design Patterns

### 1. Factory Pattern
Used in data loading to create appropriate financial data structures from various input formats.

### 2. Strategy Pattern
Risk assessment uses configurable thresholds, allowing different risk strategies for different use cases.

### 3. Repository Pattern
DatabaseManager acts as a repository, abstracting database operations from business logic.

## Error Handling

- All analysis functions return structured results with error fields
- Database operations use transactions with automatic rollback
- Invalid data is logged and skipped rather than causing failures

## Performance Considerations

1. **Batch Processing**: All tickers can be processed in a single run
2. **Lazy Loading**: Data is loaded on-demand for specific tickers
3. **Index Optimization**: Database tables have indexes on frequently queried columns
4. **Memory Management**: Large datasets are processed iteratively

## Security Notes

- No sensitive data is stored in configuration files
- Database is local SQLite (no network exposure)
- Input validation prevents SQL injection

## Future Enhancements

1. **API Integration**: Real-time financial data feeds
2. **Web Interface**: Browser-based dashboard
3. **Advanced Analytics**: Trend analysis, peer comparison
4. **Reporting Templates**: Customizable report formats
5. **Multi-database Support**: PostgreSQL, MySQL compatibility
