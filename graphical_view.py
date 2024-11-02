import pandas as pd
import matplotlib.pyplot as plt
import yaml

# Load settings from system_settings.yml to get the trading instruments
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

trading_instrument = settings.get('trading_instrument')

# Load merged data file for the specified trading instrument
file_path = f'data/{trading_instrument}_merged_data.xlsx'
merged_data = pd.read_excel(file_path)

# Plot the Closing Price with Upper and Lower Bands and Rolling Median
plt.figure(figsize=(12, 6))
plt.plot(merged_data['Datetime'], merged_data['Close_x'], label='Closing Price', color='blue')
plt.plot(merged_data['Datetime'], merged_data['Upper Band'], label='Upper Band', linestyle='--', color='red')
plt.plot(merged_data['Datetime'], merged_data['Lower Band'], label='Lower Band', linestyle='--', color='green')
plt.plot(merged_data['Datetime'], merged_data['current_median'], label='Rolling Median', color='purple')

# Add titles and labels
plt.title(f"{trading_instrument} - Closing Price with Bands and Current Median")
plt.xlabel("Date")
plt.ylabel("Price")
plt.legend()

# Show the plot
plt.tight_layout()
plt.show()
