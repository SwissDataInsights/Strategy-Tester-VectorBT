import pandas as pd
import vectorbt as vbt
import yaml
import plotly.graph_objects as go
import plotly.io as pio

pio.renderers.default = 'browser'

# Load settings
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

fix_size = 10000
trading_instrument = settings.get('trading_instrument')
risk_ratio = settings.get('risk_ratio')
stop_loss_percentage = settings.get('stop_loss_percentage')

# Load data
file_path = 'data/merged_prices.xlsx'
merged_data = pd.read_excel(file_path)

merged_data['Time'] = pd.to_datetime(merged_data['Time'])
merged_data.set_index('Time', inplace=True)

close_price_Ask = merged_data['CloseAsk'].astype(float).fillna(0)
close_price_Bid = merged_data['CloseBid'].astype(float).fillna(0)

current_median = merged_data['Median_CloseAsk_10080min'].astype(float).fillna(0)
previous_median = merged_data['Previous_Median'].astype(float).fillna(0)

upper_band = merged_data['Upper_Bollinger'].astype(float).fillna(0)
lower_band = merged_data['Lower_Bollinger'].astype(float).fillna(0)

# Calculate stop-loss and take-profit levels
SL_long = current_median - (stop_loss_percentage * (current_median - lower_band))
TP_long = upper_band

current_risk_ratio_long = (upper_band - close_price_Ask) / (upper_band - current_median)

# Long entries and exits
entries_long = (
        (current_median > previous_median) &
        (close_price_Ask > current_median) &
        (current_risk_ratio_long >= risk_ratio)
).fillna(False).astype(bool)

exits_long = (
        (current_median <= previous_median) |
        (close_price_Ask <= SL_long) |
        (close_price_Ask >= TP_long)
).fillna(False).astype(bool)

# Debug entries and exits
print(f"Number of long entries: {entries_long.sum()}")
print(f"Number of long exits: {exits_long.sum()}")

# Portfolio construction
pf = vbt.Portfolio.from_signals(
    close=close_price_Ask,
    entries=entries_long,
    exits=exits_long,
    size=fix_size,
    init_cash=10000,
    #fees=3,
    freq='D'
)

# Save trades
trades = pf.trades.records_readable
trades['Entry Timestamp'] = pd.to_datetime(trades['Entry Timestamp'])
trades.set_index('Entry Timestamp', inplace=True)

trades.reset_index(inplace=True)
trades_file_path = f'data/{trading_instrument}_trades.xlsx'
trades.to_excel(trades_file_path, index=False)
print(f"Trades saved to {trades_file_path}")

# Filter data to include only rows with valid median values
valid_data = merged_data[current_median > 0].dropna(subset=['Median_CloseAsk_10080min'])

filtered_current_median = valid_data['Median_CloseAsk_10080min']
filtered_upper_band = valid_data['Upper_Bollinger']
filtered_lower_band = valid_data['Lower_Bollinger']
filtered_close_price = valid_data['CloseAsk']

# Entries and exits positions for the chart
entries_long_positions = close_price_Ask[entries_long]
exits_long_positions = close_price_Ask[exits_long]

# System statistics
stats = pf.stats()

# Display detailed statistics
print("=== System Statistics ===")
print(stats)

# Save statistics to a file
stats_file_path = f'data/{trading_instrument}_system_statistics.txt'
with open(stats_file_path, 'w') as f:
    f.write(stats.to_string())
print(f"System statistics saved to {stats_file_path}")

# Additional specific metrics
print("\n=== Key Performance Metrics ===")
print(f"Total Return: {pf.total_return():.2%}")
print(f"Annualized Return: {pf.annualized_return():.2%}")
print(f"Max Drawdown: {pf.max_drawdown():.2%}")
print(f"Sharpe Ratio: {pf.sharpe_ratio():.2f}")
print(f"Number of Trades: {pf.trades.count()}")

# Save trades details for deeper analysis
trades_file_path = f'data/{trading_instrument}_trades_details.xlsx'
pf.trades.records_readable.to_excel(trades_file_path, index=False)
print(f"Trade details saved to {trades_file_path}")

# Portfolio plot
fig1 = pf.plot()
fig1.update_layout(
    title=f'Portfolio Performance {pd.Timestamp.now()}',
    width=1400,
    height=800
)
fig1.show()

# Additional scatter plot with entries and exits
fig2 = go.Figure()
fig2.add_scatter(
    x=filtered_current_median.index,
    y=filtered_current_median,
    mode='lines',
    name='Median',
    line=dict(dash='dash', color='blue', width=2),
    opacity=0.8
)
fig2.add_scatter(
    x=filtered_upper_band.index,
    y=filtered_upper_band,
    mode='lines',
    name='Upper Band',
    line=dict(dash='dot', color='green', width=2),
    opacity=0.8
)
fig2.add_scatter(
    x=filtered_lower_band.index,
    y=filtered_lower_band,
    mode='lines',
    name='Lower Band',
    line=dict(dash='dot', color='red', width=2),
    opacity=0.8
)
fig2.add_scatter(
    x=filtered_close_price.index,
    y=filtered_close_price,
    mode='lines',
    name='Close Price',
    line=dict(color='black', width=2),
    opacity=0.8
)
# Add markers for entries
fig2.add_scatter(
    x=entries_long_positions.index,
    y=entries_long_positions,
    mode='markers',
    name='Long Entry',
    marker=dict(symbol='triangle-up', color='green', size=10)
)
# Add markers for exits
fig2.add_scatter(
    x=exits_long_positions.index,
    y=exits_long_positions,
    mode='markers',
    name='Long Exit',
    marker=dict(symbol='triangle-down', color='red', size=10)
)
fig2.update_layout(
    title=f'Entries and Exits Positions {pd.Timestamp.now()}',
    width=1400,
    height=800
)
fig2.show()
