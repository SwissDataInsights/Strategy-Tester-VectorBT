import pandas as pd
import datetime
import vectorbt as vbt
import yaml

# Load settings from system_settings.yml
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

# Retrieve the days parameter from the settings file
days = settings.get('days', 90)  # Use 90 as a default if not found

# Define the date range
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=days)

weekly_data = vbt.YFData.download(
    ["SREN.SW"],
    missing_index="drop",
    start=start_date,
    end=end_date,
    interval="1wk")

hourly_data = vbt.YFData.download(
    ["SREN.SW"],
    missing_index="drop",
    start=start_date,
    end=end_date,
    interval="1h")

weekly_data = weekly_data.get()
hourly_data = hourly_data.get()

# Save data to a CSV file
weekly_data.to_csv('data/weekly_data.csv', index=True)
hourly_data.to_csv('data/hourly_data.csv', index=True)

# Load the data
weekly_data = pd.read_csv('data/weekly_data.csv')
hourly_data = pd.read_csv('data/hourly_data.csv')

# Convert date columns to datetime format and remove timezone information
weekly_data['Date'] = pd.to_datetime(weekly_data['Date']).dt.tz_localize(None)
hourly_data['Datetime'] = pd.to_datetime(hourly_data['Datetime']).dt.tz_localize(None)

# Sort data by date
weekly_data = weekly_data.sort_values('Date')
hourly_data = hourly_data.sort_values('Datetime')

# Use merge_asof to align each hourly row with the most recent weekly data
merged_data = pd.merge_asof(
    hourly_data,
    weekly_data,
    left_on='Datetime',
    right_on='Date',
    direction='backward'
)

# Drop the unnecessary columns
merged_data = merged_data.drop(columns=['Dividends_x', 'Stock Splits_x', 'Dividends_y', 'Stock Splits_y'])

# Specify the columns you want to round
columns_to_round = ['Open_x', 'High_x', 'Low_x', 'Close_x', 'Open_y', 'High_y', 'Low_y', 'Close_y']

# Round specified columns to 2 decimal places
merged_data[columns_to_round] = merged_data[columns_to_round].round(2)

# Save merged data to an Excel file
merged_data.to_excel('data/merged_data.xlsx', index=False)
