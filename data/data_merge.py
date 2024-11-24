import pandas as pd
import yaml
import os

# Load settings
settings_path = os.path.join("..", "system_settings.yml")
with open(settings_path, 'r') as file:
    settings = yaml.safe_load(file)

# Load rolling median window size and band width factor from settings
median_data_60min = settings.get('median_data_60min', 6)
median_data_1440min = settings.get('median_data_1440min', 6)
median_data_10080min = settings.get('median_data_10080min', 6)
band_width_factor = settings.get('band_width_factor', 2)

# Function to calculate rolling median for a specified column
def calculate_rolling_median(data, column_name='CloseAsk', window=6):
    median_column_name = f'Median_{column_name}'  # Name for median column
    data[median_column_name] = data[column_name].rolling(window=window).median()
    return data

# Function to calculate Bollinger Bands based on median and rolling standard deviation
def calculate_bollinger_bands(data, median_column='Median_CloseAsk', column_name='CloseAsk', window=6, width_factor=2):
    # Calculate rolling standard deviation
    data['Rolling_Std'] = data[column_name].rolling(window=window).std()

    # Calculate upper and lower bands
    data['Upper_Bollinger'] = (data[median_column] + width_factor * data['Rolling_Std']).round(5)
    data['Lower_Bollinger'] = (data[median_column] - width_factor * data['Rolling_Std']).round(5)
    return data

# Load data from CSV files, ensuring timezone is removed from 'Time' column
data_5min = pd.read_csv("historical_prices_5min.csv", parse_dates=["Time"])
data_1440min = pd.read_csv("historical_prices_1440min.csv", parse_dates=["Time"])
data_10080min = pd.read_csv("historical_prices_10080min.csv", parse_dates=["Time"])

data_5min['Time'] = pd.to_datetime(data_5min['Time']).dt.tz_localize(None)
data_1440min['Time'] = pd.to_datetime(data_1440min['Time']).dt.tz_localize(None)
data_10080min['Time'] = pd.to_datetime(data_10080min['Time']).dt.tz_localize(None)

# Calculate rolling medians for each dataset independently
data_5min = calculate_rolling_median(data_5min, column_name='CloseAsk', window=median_data_60min)
data_1440min = calculate_rolling_median(data_1440min, column_name='CloseAsk', window=median_data_1440min)
data_10080min = calculate_rolling_median(data_10080min, column_name='CloseAsk', window=median_data_10080min)

# Add the "Previous_Median" column to weekly data (10080min) by shifting the median column by 1 period
data_10080min['Previous_Median'] = data_10080min['Median_CloseAsk'].shift(1)

# Calculate Bollinger Bands for weekly (10080min) data
data_10080min = calculate_bollinger_bands(data_10080min, median_column='Median_CloseAsk', column_name='CloseAsk',
                                          window=median_data_10080min, width_factor=band_width_factor)

# Sort data by "Time" column to ensure alignment for merging
data_5min = data_5min.sort_values(by="Time")
data_1440min = data_1440min.sort_values(by="Time")
data_10080min = data_10080min.sort_values(by="Time")

# Merge datasets using 'Time' column with backward matching
# First merge 60min data with 1440min data, then merge the result with 10080min data
data_60min_with_1440 = pd.merge_asof(data_5min, data_1440min, on="Time", direction="backward",
                                     suffixes=('', '_1440min'))
merged_data = pd.merge_asof(data_60min_with_1440, data_10080min, on="Time", direction="backward",
                            suffixes=('', '_10080min'))

# Save the final merged dataset to Excel
merged_data.to_excel("merged_prices.xlsx", index=False)
print("Dane zostały zapisane do pliku merged_prices.xlsx")
