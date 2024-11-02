import pandas as pd
import vectorbt as vbt
import yaml
import datetime
import plotly.io as pio

pio.renderers.default = 'browser'

# Load settings from system_settings.yml to get the trading instruments
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

days = settings.get('days')
trading_instrument = settings.get('trading_instrument')
risk_ratio = settings.get('risk_ratio')
stop_loss_percentage = settings.get('stop_loss_percentage')

# Load merged data file for the specified trading instrument
file_path = f'data/{trading_instrument}_merged_data.xlsx'
merged_data = pd.read_excel(file_path)

# Ensure 'Datetime' is in datetime format and set it as the index if necessary
merged_data['Datetime'] = pd.to_datetime(merged_data['Datetime'])
merged_data.set_index('Datetime', inplace=True)

# Extract relevant columns and calculate additional metrics
close_price = merged_data['Close_x']
max_price = merged_data['High_x']
low_price = merged_data['Low_x']
current_median = merged_data['current_median']
previous_median = merged_data['previous_median']
current_risk_ratio = round((current_median / close_price),4)
upper_band = merged_data['Upper Band']
lower_band = merged_data['Lower Band']

# Define entry and exit conditions for long and short positions
entries_long = (
    (current_median > previous_median) &
    (max_price > current_median) &
    (current_risk_ratio >= risk_ratio) &
    (current_risk_ratio <= 1)
)

SL_long = round(current_median - (stop_loss_percentage * (current_median - lower_band)));2
TP_long = upper_band

exits_long = (
    (current_median <= previous_median) |  # Warunek 1: current_median <= previous_median
    (low_price <= SL_long) |              # Warunek 2: low_price <= SL_long
    (max_price >= TP_long)                # Warunek 3: max_price >= TP_long
)

entries_short = (
    (current_median < previous_median) &
    (low_price < current_median) &
    (current_risk_ratio >= risk_ratio) &
    (current_risk_ratio <= 1)
)

SL_short = round(current_median + (stop_loss_percentage * (current_median - upper_band)));2
TP_short = lower_band

exits_short = (
    (current_median >= previous_median) |
    (max_price >= SL_short) |
    (low_price <= TP_short)
)

# Add diagnostic columns to the DataFrame for analysis
merged_data['current_median'] = current_median
merged_data['previous_median'] = previous_median
merged_data['current_risk_ratio'] = current_risk_ratio
merged_data['entries_long'] = entries_long
merged_data['exits_long'] = exits_long
merged_data['SL_long'] = SL_long
merged_data['TP_long'] = TP_long
merged_data['entries_short'] = entries_short
merged_data['exits_short'] = exits_short
merged_data['SL_short'] = SL_short
merged_data['TP_short'] = TP_short

# Save the diagnostic data to an Excel file
diagnostic_file_path = f'data/{trading_instrument}_diagnostics.xlsx'
merged_data.to_excel(diagnostic_file_path, index=True)

print(f"Diagnostic information saved to {diagnostic_file_path}")

# Backtest with vectorbt using the entry and exit signals
pf = vbt.Portfolio.from_signals(close_price, entries_long, exits_long, entries_short, exits_short)

# Print statistics and plot the portfolio performance
print(pf.stats())
pf.plot().show()  # Show portfolio plot in the browser

print(pf.total_return())
