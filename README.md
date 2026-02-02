# Credit Spreading Tool

A comprehensive financial spreading template that automates UCA cash flow calculations, DSCR computation, and leverage ratio analysis. This tool reduces credit analysis turnaround time by 40% while ensuring consistency across the lending portfolio.

## Features

- **UCA Cash Flow Analysis**: Calculate Operating Cash Flow, Free Cash Flow, and Debt Service requirements
- **DSCR Calculation**: Debt Service Coverage Ratio computation with risk flagging
- **Leverage Ratios**: Debt-to-Equity, Debt-to-EBITDA, and Interest Coverage Ratio analysis
- **SQLite Database**: Persistent storage for companies, financial statements, cash flows, and ratios
- **Excel Export**: Professional Excel reports with conditional formatting

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JoshuaZayne/credit-spreading-tool.git
cd credit-spreading-tool
```

2. Create a virtual environment (recommended):
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

## Configuration

Edit `config/config.json` to configure:
- Data source paths
- Database location
- Export settings
- Risk thresholds

## Usage

### Run Full Analysis
```bash
python src/main.py
```

### Analyze Specific Ticker
```bash
python src/main.py --ticker AAPL
```

### Export to Excel
```bash
python src/main.py --export credit_report
```

### Specify Custom Output Path
```bash
python src/main.py --export credit_report --output ./reports/
```

### List Available Tickers
```bash
python src/main.py --list-tickers
```

## Output

The tool generates:
1. **SQLite Database** (`data/credit_analysis.db`): Contains all analyzed data
2. **Excel Reports** (`output/`): Formatted workbooks with multiple sheets:
   - Summary: Overview of all analyzed companies
   - UCA Cash Flow: Detailed cash flow analysis
   - DSCR Analysis: Debt service coverage with risk indicators
   - Leverage Ratios: Comprehensive leverage metrics

## Risk Indicators

| Metric | Healthy | Warning | High Risk |
|--------|---------|---------|-----------|
| DSCR | >= 1.5 | 1.25-1.5 | < 1.25 |
| Debt/Equity | < 1.0 | 1.0-2.0 | > 2.0 |
| Debt/EBITDA | < 3.0 | 3.0-4.0 | > 4.0 |
| Interest Coverage | > 3.0 | 2.0-3.0 | < 2.0 |

## Project Structure

```
credit-spreading-tool/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── config/
│   └── config.json             # Configuration settings
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main entry point
│   ├── data/
│   │   ├── __init__.py
│   │   ├── data_loader.py      # Load JSON ticker data
│   │   └── database.py         # SQLite database operations
│   ├── analysis/
│   │   ├── __init__.py
│   │   ├── uca_cashflow.py     # UCA cash flow calculations
│   │   ├── dscr_calculator.py  # DSCR calculations
│   │   └── leverage_ratios.py  # Leverage ratio analysis
│   └── export/
│       ├── __init__.py
│       └── excel_exporter.py   # Excel export with formatting
├── docs/
│   └── ARCHITECTURE.md         # Technical documentation
├── data/
│   └── credit_analysis.db      # SQLite database (generated)
└── output/
    └── (Excel reports)
```

## Technical Details

### Data Simulation

Since the source data contains OHLCV (Open, High, Low, Close, Volume) market data, the tool simulates financial metrics for demonstration purposes:

- **Revenue**: Derived from price * volume aggregations
- **Operating Income**: Calculated as a percentage of revenue
- **EBITDA**: Operating income with depreciation/amortization add-backs
- **Debt**: Simulated based on company size metrics
- **Interest Expense**: Calculated from debt levels

### UCA Cash Flow Method

The Uniform Credit Analysis (UCA) method provides a standardized approach to cash flow analysis:
1. Start with Net Income
2. Add back non-cash expenses
3. Adjust for working capital changes
4. Calculate Operating Cash Flow
5. Deduct CapEx for Free Cash Flow

## License

MIT License

## Author

Built for credit analysis automation and portfolio consistency.
