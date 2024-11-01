import pandas as pd
import vectorbt as vbt
from openbb import obb

# Trading instrument and interval configuration
trading_instrument = 'EURUSD'
median_interval = 1440

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
    start_date='2024-08-01',  # start date
    end_date='2024-10-31',    # end date
    provider='yfinance'       # Data provider
)

# Convert the downloaded data to a DataFrame
weekly_data_df = weekly_data.to_dataframe()

# Calculate the median from the specified number of periods
current_median = round(weekly_data_df['close'].tail(median_periods).median(), 2)

# Calculate the median from the previous period
previous_median = round(weekly_data_df['close'].iloc[-(median_periods + 1):-1].median(), 2)

# Sample values for calculations (to be dynamically updated in practice)
current_price = 1.0856
lower_band = 1.0750
upper_band = 1.0900

# Calculate the current risk ratio
current_risk_ratio = round(current_median / current_price, 5)

# Calculate stop loss (SL) and take profit (TP) values for long and short positions
SL_long = round(current_median - (stop_loss_percentage * (current_median - lower_band)), 5)
TP_long = upper_band

SL_short = round(current_median + (stop_loss_percentage * (upper_band - current_median)), 5)
TP_short = lower_band

# Output calculated values for verification
print(f"Current weekly median: {current_median}")
print(f"Previous weekly median: {previous_median}")
print(f"Current Risk Ratio: {current_risk_ratio}")
print(f"SL Long: {SL_long}, TP Long: {TP_long}")
print(f"SL Short: {SL_short}, TP Short: {TP_short}")
