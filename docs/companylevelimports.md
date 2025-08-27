
# EIA Crude Oil Import Analysis System

## overall analysis from claude:

    Deep Analysis of EIA Company-Level Crude Oil Imports Data

    Based on my comprehensive analysis of the companylevelimports_crude.csv file and research on crude oil fundamental analysis, here's 
    my plan to help you leverage this data for trading and analysis:

    Proposed Analysis & Trading System

    1. Create a Monitoring Dashboard that tracks:
      - Real-time import volume trends by company and country
      - API gravity and sulfur content shifts (quality arbitrage opportunities)
      - PADD regional imbalances (inter-regional spread trading)
      - Company-specific import dependencies (risk assessment)
    2. Develop Trading Signals based on:
      - Supply Disruption Alerts: Monitor sudden drops in imports from specific countries/companies
      - Quality Mix Changes: Track shifts from heavy/sour to light/sweet crude (impacts crack spreads)
      - Seasonal Patterns: Exploit the May/January peak import periods
      - Regional Arbitrage: Identify PADD imbalances (e.g., PADD 3 Gulf Coast heavy crude vs PADD 1 East Coast light crude preferences)
    3. Build Fundamental Analysis Tools:
      - Refinery Matching Algorithm: Match crude quality (API/sulfur) to specific refineries' optimal configurations
      - Import Dependency Index: Calculate company vulnerability to supply disruptions
      - Crack Spread Calculator: Estimate refinery margins based on imported crude quality
      - Market Concentration Tracker: Monitor top 5 companies controlling 42% of imports
    4. Create Predictive Models for:
      - Forecasting import volumes based on seasonal patterns
      - Predicting quality mix changes based on price differentials
      - Estimating refinery utilization from import patterns
    5. Generate Regular Reports covering:
      - Month-over-month import changes by company/country
      - Quality arbitrage opportunities (heavy/sour vs light/sweet spreads)
      - Regional supply/demand imbalances
      - Risk alerts for supply concentration

    

## Overview
Comprehensive analysis system for EIA company-level crude oil imports data, providing fundamental analysis tools for trading insights and market intelligence.

## Data Structure
All data files are stored in `/data/cli/`:
- `companylevelimports_crude.parquet` - Main crude oil import data (2017-2025)
- `companylevelimports.parquet` - General petroleum imports data

## Components

### 1. Core Analyzer (`crude_import_analyzer.py`)
Main analysis engine providing:
- **Market Overview**: Volume tracking, company/country statistics
- **Supply Disruption Detection**: Identifies significant import drops
- **Quality Arbitrage Analysis**: Tracks API gravity and sulfur content shifts
- **Refinery Dependency Assessment**: Calculates concentration risk
- **Seasonal Pattern Detection**: Identifies monthly trading opportunities
- **Trading Signal Generation**: Automated signal generation based on multiple factors

### 2. Crack Spread Calculator (`crack_spread_calculator.py`)
Advanced refinery economics module:
- **Simple Crack Spreads**: 3-2-1 and 5-3-2 ratio calculations
- **Quality-Adjusted Spreads**: Accounts for crude quality differences
- **Refinery Yield Modeling**: Estimates product yields by crude type
- **Profitability Analysis**: Calculates margins by import source
- **Trading Recommendations**: Z-score based entry/exit signals

### 3. Visualization Module (`visualization.py`)
Comprehensive charting and reporting:
- **12-Panel Dashboard**: Complete visual analysis
- **7 Analytical Tables**: Detailed tabular insights
- **Excel Export**: All tables exportable to Excel
- **Key Statistics Summary**: Quick overview metrics

## Key Insights from Data

### Market Structure
- **117,099** import records spanning 2017-2025
- **20.56 billion barrels** total import volume
- **122** unique importing companies
- **57** source countries

### Quality Distribution
- **60.5%** Heavy crude (<25° API)
- **74.8%** Sour crude (>1% sulfur)
- Recent trend toward heavier, more sour crude

### Regional Dependencies
- **PADD 2 (Midwest)**: 41.7% of imports, 100% from Canada
- **PADD 3 (Gulf Coast)**: 25.2% of imports, diversified sources
- **PADD 5 (West Coast)**: 17.8% of imports, Pacific basin focus

### Market Concentration
- Top 5 companies control **42%** of imports
- Phillips 66: 12.9% market share
- Canada supplies **56%** of total US imports

## Charts and Tables Generated

### Visualizations (12-panel dashboard)
1. **Top Importers Bar Chart** - Volume by company
2. **Country Sources Pie Chart** - Import distribution
3. **PADD Regional Distribution** - Regional import patterns
4. **Volume Time Series** - Historical trends
5. **Quality Heatmap** - Country crude characteristics
6. **API vs Sulfur Scatter** - Quality distribution
7. **Monthly Seasonality** - Seasonal patterns
8. **Country Quality Profile** - Detailed quality mix
9. **Company Dependency Matrix** - Company-country relationships
10. **Country Import Trends** - Time series by country
11. **Quality Evolution** - API/sulfur trends over time
12. **Concentration Risk Chart** - Herfindahl index analysis

### Tables (7 comprehensive tables)
1. **Top Importers Summary** - Company rankings with quality metrics
2. **Country Analysis** - Source country statistics
3. **PADD Summary** - Regional breakdown
4. **Quality Distribution** - API/sulfur matrix
5. **Monthly Trends** - Recent import patterns
6. **Company-Country Dependencies** - Percentage matrix
7. **Year-over-Year Trends** - Annual comparisons

## Trading Signals & Opportunities

### Current Signals (as of latest data)
1. **Supply Disruptions**: Algeria (-100%), Peru (-100%), Angola (-70%)
   - Signal: BULLISH WTI futures (short-term)
   
2. **Quality Arbitrage**: Shift to heavier/sour crude
   - Light-sweet crack spread: $18.70/bbl
   - Heavy-sour crack spread: -$0.65/bbl
   - Signal: Long light products, short heavy products

3. **Seasonal Pattern**: May peak vs November trough (7.5% spread)
   - Signal: Calendar spread opportunities

4. **Regional Imbalances**: PADD 2 oversupplied
   - Signal: WTI-LLS spread compression

## Usage

### Quick Analysis
```python
from crude_import_analyzer import CrudeImportAnalyzer

# Initialize analyzer (uses default data path)
analyzer = CrudeImportAnalyzer()

# Generate comprehensive report
report = analyzer.generate_report()
print(report)

# Get trading signals
signals = analyzer.generate_trading_signals()
for signal in signals:
    print(f"{signal['signal_type']}: {signal['direction']}")
```

### Visualization
```python
from visualization import CrudeImportVisualizer

# Create visualizer
viz = CrudeImportVisualizer()

# Generate dashboard
viz.create_dashboard(save_path='dashboard.png')

# Generate tables
tables = viz.generate_tables(save_excel=True, excel_path='analysis.xlsx')

# Print key statistics
viz.print_key_statistics()
```

### Crack Spread Analysis
```python
from crack_spread_calculator import CrackSpreadCalculator

calculator = CrackSpreadCalculator()

# Calculate 3-2-1 spread
spread = calculator.calculate_simple_crack_spread(
    crude_price=80,
    gasoline_price=110,
    heating_oil_price=105,
    ratio='3-2-1'
)
print(f"3-2-1 Crack Spread: ${spread:.2f}/barrel")
```

### Running Full Analysis
```bash
# Run complete analysis with all components
python run_analysis.py
```

## Data Updates
The system expects monthly updates from EIA's company-level imports data. Update the CSV files in `/data/cli/` when new data becomes available.

## Requirements
- pandas
- numpy
- matplotlib
- seaborn
- openpyxl (for Excel export)

## Output Files
- `crude_analysis_report_[timestamp].txt` - Detailed text report
- `dashboard.png` - 12-panel visualization dashboard
- `analysis_tables.xlsx` - All tables in Excel format

## Future Enhancements
1. Real-time price feed integration
2. Machine learning predictions
3. Interactive web dashboard
4. Automated alert system
5. API integration with trading platforms