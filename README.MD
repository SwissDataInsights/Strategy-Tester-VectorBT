# Strategy Tester with VectorBT

This project implements a trading strategy tester using **VectorBT** to analyze historical market data, execute signals based on Bollinger Bands and rolling medians, and evaluate trading performance.

## Features
- **Data Preparation**: Combines multiple time intervals into a unified dataset.
- **Rolling Median & Bollinger Bands**: Calculates rolling medians and Bollinger Bands for market data.
- **Trading Signals**: Generates long entries and exits based on custom logic.
- **Performance Analysis**: Evaluates portfolio statistics and generates visualizations.
- **Trades Export**: Exports trade details and statistics to Excel files for detailed analysis.

## Requirements
Install the required Python libraries listed in `requirements.txt`:
```bash
pip install -r requirements.txt
```

### Main Libraries:
- `pandas`: For data manipulation.
- `vectorbt`: For portfolio backtesting and performance analysis.
- `yaml`: For configuration file management.
- `plotly`: For interactive visualizations.

## Configuration
The project uses a YAML file (`system_settings.yml`) to define key parameters:
- `trading_instrument`: The symbol of the instrument being traded.
- `risk_ratio`: The minimum acceptable risk/reward ratio for trades.
- `stop_loss_percentage`: The percentage for stop-loss calculation.
- `median_data_10080min`: The rolling median window for weekly data.
- `band_width_factor`: Multiplier for Bollinger Band widths.

Example `system_settings.yml`:
```yaml
trading_instrument: EURUSD
risk_ratio: 1.5
stop_loss_percentage: 0.02
median_data_60min: 6
median_data_1440min: 6
median_data_10080min: 6
band_width_factor: 2
```

## How to Run
### Step 1: Data Preparation
Use `data_merge.py` to prepare and merge historical market data across different time intervals:
```bash
python data_merge.py
```
This script generates the file `merged_prices.xlsx`, which is used for strategy testing.

### Step 2: Strategy Testing
Run the main strategy script:
```bash
python vectorbt_strategy_long.py
```
This script:
1. Loads the prepared data (`merged_prices.xlsx`).
2. Computes rolling medians and Bollinger Bands.
3. Identifies long entry and exit signals.
4. Executes trades using VectorBT's portfolio management tools.
5. Saves trade details and performance metrics.

### Outputs:
- **Trades File**: Saved as `{trading_instrument}_trades.xlsx` in the `data/` folder.
- **Performance Statistics**: Saved as `{trading_instrument}_system_statistics.txt` in the `data/` folder.
- **Portfolio Visualizations**: Interactive charts displayed in the browser.

### Key Metrics:
- Total Return
- Annualized Return
- Maximum Drawdown
- Sharpe Ratio
- Number of Trades

## Visualization
The script generates two main charts:
1. **Portfolio Performance**: Shows portfolio growth over time.
2. **Entries and Exits**: Highlights entry and exit points on a price chart with Bollinger Bands and rolling medians.

## File Structure
```
.
├── vectorbt_strategy_long.py       # Main strategy script
├── data_merge.py                   # Data merging script
├── system_settings.yml             # Configuration file
├── requirements.txt                # List of dependencies
├── data/
│   ├── historical_prices_5min.csv  # 5-minute interval data
│   ├── historical_prices_1440min.csv  # Daily interval data
│   ├── historical_prices_10080min.csv # Weekly interval data
│   ├── merged_prices.xlsx          # Final merged dataset
│   ├── {trading_instrument}_trades.xlsx  # Trade records
│   ├── {trading_instrument}_system_statistics.txt  # Performance statistics
```

## Customization
Adjust the logic for entries and exits in `vectorbt_strategy_long.py` to experiment with different strategies. Update settings in `system_settings.yml` to tweak parameters such as risk ratio, stop-loss percentage, and Bollinger Band widths.

## License
This project is licensed under the MIT License. Feel free to use and modify it.