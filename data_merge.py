import pandas as pd
import datetime
import vectorbt as vbt
import yaml

# Load settings from system_settings.yml
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

# Retrieve the days parameter from the settings file
days = settings.get('days')
band_width_factor = settings.get('band_width_factor')
median_periods = settings.get('median_periods')
trading_instrument = settings.get('trading_instrument')

# Define the date range
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=days)

weekly_data = vbt.YFData.download(
    trading_instrument,
    missing_index="drop",
    start=start_date,
    end=end_date,
    interval="1wk")

hourly_data = vbt.YFData.download(
    trading_instrument,
    missing_index="drop",
    start=start_date,
    end=end_date,
    interval="1h")

hourly_data = hourly_data.get()
"""
weekly_data = weekly_data.get()

# Calculate the rolling median for the specified number of periods
weekly_data['Rolling Median'] = round(weekly_data['Close'].rolling(window=median_periods).median(),2)

# Calculate the rolling standard deviation for the specified number of periods
weekly_data['Rolling Std Dev'] = weekly_data['Close'].rolling(window=median_periods).std()

# Calculate the upper and lower Bollinger Bands
weekly_data['Upper Band'] = (weekly_data['Rolling Median'] + band_width_factor * weekly_data['Rolling Std Dev']).round(2)
weekly_data['Lower Band'] = (weekly_data['Rolling Median'] - band_width_factor * weekly_data['Rolling Std Dev']).round(2)

# Remove the Rolling Std Dev column if you don't want to keep it in the final output
weekly_data = weekly_data.drop(columns=['Rolling Std Dev'])

# Save data to a CSV file
weekly_data.to_csv('data/weekly_data.csv', index=True)
"""

hourly_data.to_csv('data/hourly_data.csv', index=True)

# Load the data
weekly_data = pd.read_csv('data/weekly_data.csv')
hourly_data = pd.read_csv('data/hourly_data.csv')

# Convert date columns to datetime format and remove timezone information
weekly_data['Datetime'] = pd.to_datetime(weekly_data['Datetime']).dt.tz_localize(None)
hourly_data['Datetime'] = pd.to_datetime(hourly_data['Datetime']).dt.tz_localize(None)

# Sort data by date
weekly_data = weekly_data.sort_values('Datetime')
hourly_data = hourly_data.sort_values('Datetime')

# Use merge_asof to align each hourly row with the most recent weekly data
merged_data = pd.merge_asof(
    hourly_data,
    weekly_data,
    left_on='Datetime',
    right_on='Datetime',
    direction='backward'
)

# Drop the unnecessary columns
#merged_data = merged_data.drop(columns=['Dividends_x', 'Stock Splits_x', 'Dividends_y', 'Stock Splits_y'])

# Specify the columns you want to round
columns_to_round = ['Open_x', 'High_x', 'Low_x', 'Close_x', 'Open_y', 'High_y', 'Low_y', 'Close_y']

# Round specified columns to 2 decimal places
merged_data[columns_to_round] = merged_data[columns_to_round].round(2)

# Save merged data to an Excel file
merged_data.to_excel(f'data/{trading_instrument}_merged_data.xlsx', index=False)