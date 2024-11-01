import pandas as pd
import vectorbt as vbt
from openbb import obb
import matplotlib.pyplot as plt

# Basic variables
fee = 0.001  # Transaction fee 0.1%
risk_ratio = 0.98
available_capital = 10000
band_width_factor = 1.5
median_periods = 6
risk_level = 0.004
stop_loss_percentage = 0.30

# Download weekly data
weekly_data = obb.equity.price.historical(
    symbol='SREN.SW',
    interval='1W',
    start_date='2024-01-01',  # start date
    end_date='2024-10-31',  # end date
    provider='yfinance'  # Data provider
)

# Download 5-minute data for a smaller range (one month)
try:
    one_minute_data = obb.equity.price.historical(
        symbol='SREN.SW',
        interval='5m',
        start_date='2024-09-01',  # start date
        end_date='2024-09-30',  # end date
        provider='yfinance'  # Data provider
    )
    # Download 1-hour data
    one_hour_data = obb.equity.price.historical(
        symbol='SREN.SW',
        interval='1h',
        start_date='2024-09-01',  # start date
        end_date='2024-09-30',  # end date
        provider='yfinance'  # Data provider
    )
    # Convert the downloaded data to DataFrame
    one_minute_data_df = one_minute_data.to_dataframe()
    one_minute_data_df = one_minute_data_df.round(2)
    # Add a column to the one-minute data indicating the week it belongs to
    one_minute_data_df['week'] = pd.to_datetime(one_minute_data_df.index).to_period('W')

except Exception as e:
    print(f"Error downloading 5-minute data: {e}")
    one_minute_data_df = pd.DataFrame()  # Empty DataFrame to handle gracefully

# Convert the downloaded data to DataFrames
weekly_data_df = weekly_data.to_dataframe()
weekly_data_df = weekly_data_df.round(2)

# Convert 1-hour data to DataFrame
one_hour_data_df = one_hour_data.to_dataframe()
one_hour_data_df = one_hour_data_df.round(2)

# Add a column to the one-minute data indicating the week it belongs to
one_minute_data_df['week'] = pd.to_datetime(one_minute_data_df.index).to_period('W')

# Add a column to the weekly data indicating the week it belongs to
weekly_data_df['week'] = pd.to_datetime(weekly_data_df.index).to_period('W')

# Merge weekly data with minute-level data by assigning each minute to the appropriate week
merged_df = pd.merge(one_minute_data_df, weekly_data_df, on='week', suffixes=('_minute', '_weekly'))

# Calculate the median from the specified number of periods
weekly_data_df['median'] = weekly_data_df['close'].rolling(window=median_periods).median()

# Calculate the upper and lower bands
weekly_data_df['band_upper'] = round(
    weekly_data_df['median'] + (band_width_factor * (weekly_data_df['median'] - weekly_data_df['close'].min())), 2)
weekly_data_df['band_lower'] = round(
    weekly_data_df['median'] - (band_width_factor * (weekly_data_df['median'] - weekly_data_df['close'].min())), 2)

# Calculate the current risk ratio
current_median = round(weekly_data_df['median'].iloc[-1], 2)
previous_median = round(weekly_data_df['median'].iloc[-2], 2)
current_price = one_minute_data_df['close'].iloc[-1]
current_risk_ratio = round(current_median / current_price, 2)

# Calculate stop loss (SL) and take profit (TP) values for long and short positions
SL_long = round(current_median - (stop_loss_percentage * (current_median - weekly_data_df['band_lower'].iloc[-1])), 5)
TP_long = round(weekly_data_df['band_upper'].iloc[-1], 2)

SL_short = round(current_median + (stop_loss_percentage * (weekly_data_df['band_upper'].iloc[-1] - current_median)), 5)
TP_short = round(weekly_data_df['band_lower'].iloc[-1], 2)

# Output calculated values for verification
print(f"Current weekly median: {current_median}")
print(f"Previous weekly median: {previous_median}")
print(f"Band Upper: {weekly_data_df['band_upper'].iloc[-1]}, Band Lower: {weekly_data_df['band_lower'].iloc[-1]}")
print(f"Current Risk Ratio: {current_risk_ratio}")
print(f"SL Long: {SL_long}, TP Long: {TP_long}")
print(f"SL Short: {SL_short}, TP Short: {TP_short}")

# Plot the price, median, bands, and 1-hour data
plt.figure(figsize=(12, 6))
plt.plot(one_hour_data_df.index, one_hour_data_df['close'], label='Price (1-Hour Data)', color='blue', alpha=0.5)
plt.plot(weekly_data_df.index, weekly_data_df['median'], label='Median', color='orange', linestyle='--')
plt.plot(weekly_data_df.index, weekly_data_df['band_upper'], label='Upper Band', color='green', linestyle='-.')
plt.plot(weekly_data_df.index, weekly_data_df['band_lower'], label='Lower Band', color='red', linestyle='-.')

# Plot high and low values for each week
plt.scatter(weekly_data_df.index, weekly_data_df['high'], label='Weekly High', color='purple', marker='^', alpha=0.7)
plt.scatter(weekly_data_df.index, weekly_data_df['low'], label='Weekly Low', color='brown', marker='v', alpha=0.7)

plt.title('SwissRe Weekly Median, Bands, and High/Low')
plt.xlabel('Date')
plt.ylabel('Price')
plt.ylim(70, 160)
plt.legend()
plt.grid(True)
plt.show()
