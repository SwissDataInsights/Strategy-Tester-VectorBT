import vectorbt as vbt
import pandas as pd
import numpy as np
import yaml
import datetime
import plotly.io as pio

pio.renderers.default = 'browser'

# Load settings from system_settings.yml for initial parameter ranges
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

trading_instrument = settings.get('trading_instrument')

# Set up parameter ranges
band_width_factor_range = np.arange(1.0, 2.5, step=0.1)
stop_loss_percentage_range = np.arange(0.01, 0.30, step=0.01)
median_periods_range = np.arange(3, 10, step=1, dtype=int)
risk_ratio_range = np.arange(0.8, 1.0, step=0.01)

# Define start and end times for fetching data
end_time = datetime.datetime.now()
start_time = end_time - datetime.timedelta(days=60)

# Load merged data file for the specified trading instrument
file_path = f'data/{trading_instrument}_merged_data.xlsx'
merged_data = pd.read_excel(file_path)

# Ensure 'Datetime' is in datetime format and set it as the index if necessary
merged_data['Datetime'] = pd.to_datetime(merged_data['Datetime'])
merged_data.set_index('Datetime', inplace=True)

# Extract relevant columns and calculate additional metrics
price_data = merged_data['Close_x']

# Define custom indicator function for entries and exits
def custom_strategy(close, band_width_factor, stop_loss_percentage, median_periods, risk_ratio):
    # Calculate rolling median and bands based on parameters
    rolling_median = close.rolling(window=median_periods).median()
    rolling_std_dev = close.rolling(window=median_periods).std()
    upper_band = rolling_median + band_width_factor * rolling_std_dev
    lower_band = rolling_median - band_width_factor * rolling_std_dev

    # Conditions for long and short entries based on risk ratio and bands
    risk_ratio_calc = rolling_median / close
    entries_long = (rolling_median > rolling_median.shift(1)) & \
                   (close < upper_band) & \
                   (risk_ratio_calc >= risk_ratio) & \
                   (risk_ratio_calc <= 100)
    exits_long = (rolling_median <= rolling_median.shift(1)) | \
                 (close <= (rolling_median - stop_loss_percentage * (rolling_median - lower_band))) | \
                 (close >= upper_band)

    entries_short = (rolling_median < rolling_median.shift(1)) & \
                    (close > lower_band) & \
                    (risk_ratio_calc >= risk_ratio) & \
                    (risk_ratio_calc <= 100)
    exits_short = (rolling_median >= rolling_median.shift(1)) | \
                  (close >= (rolling_median + stop_loss_percentage * (upper_band - rolling_median))) | \
                  (close <= lower_band)

    return entries_long.astype(int) - exits_short.astype(int)  # Returns 1 for entry, -1 for exit


# Use IndicatorFactory to create custom strategy indicator
ind = vbt.IndicatorFactory(
    class_name="OptimizedStrategy",
    short_name="opt_strat",
    input_names=["close"],
    param_names=["band_width_factor", "stop_loss_percentage", "median_periods", "risk_ratio"],
    output_names=["signal"]
).from_apply_func(
    custom_strategy,
    keep_pd=True
)

# Run optimization with all parameter combinations
res = ind.run(
    price_data,
    band_width_factor=band_width_factor_range,
    stop_loss_percentage=stop_loss_percentage_range,
    median_periods=median_periods_range,
    risk_ratio=risk_ratio_range,
    param_product=True
)

# Define entries and exits based on the indicator signals
entries = res.signal == 1.0
exits = res.signal == -1.0

# Backtest with optimized parameters
pf = vbt.Portfolio.from_signals(price_data, entries, exits)

# Calculate and print total returns
returns = pf.total_return()

# Display heatmap of returns based on two selected parameters (e.g., `band_width_factor` and `stop_loss_percentage`)
fig = returns.vbt.heatmap(
    x_level="opt_strat_band_width_factor",
    y_level="opt_strat_stop_loss_percentage",
    trace_kwargs=dict(
        colorbar=dict(title="Total Return")  # Ustawienie tytułu dla skali kolorów
    )
)
fig.show()

# Print optimal return and corresponding parameters
print("Max Return:", returns.max())
print("Best Parameter Set:", returns.idxmax())
