import pandas as pd
import vectorbt as vbt
import yaml
import plotly.io as pio

pio.renderers.default = 'browser'

with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

fix_size = 10

trading_instrument = settings.get('trading_instrument')
risk_ratio = settings.get('risk_ratio')
stop_loss_percentage = settings.get('stop_loss_percentage')
#risk_level = settings.get('risk_level')

file_path = 'data/merged_prices.xlsx'
merged_data = pd.read_excel(file_path)

merged_data['Time'] = pd.to_datetime(merged_data['Time'])
merged_data.set_index('Time', inplace=True)

close_price = merged_data['CloseAsk'].astype(float).fillna(0)
current_median = merged_data['Median_CloseAsk_10080min'].astype(float).fillna(0)
previous_median = merged_data['Previous_Median'].astype(float).fillna(0)
upper_band = merged_data['Upper_Bollinger'].astype(float).fillna(0)
lower_band = merged_data['Lower_Bollinger'].astype(float).fillna(0)

SL_long = current_median - (stop_loss_percentage * (current_median - lower_band))
TP_long = upper_band

SL_short = current_median + (stop_loss_percentage * (upper_band - current_median))
TP_short = lower_band

current_risk_ratio_long = round(current_median / close_price, 3).fillna(0)
current_risk_ratio_short = round(close_price / current_median, 3).fillna(0)

entries_long = (
    (current_median > previous_median) &
    (close_price > current_median)
    #(current_risk_ratio_long >= risk_ratio) &
    #(current_risk_ratio_long < 1)
).fillna(False).astype(bool)

exits_long = (
    (close_price <= SL_long) |
    (close_price >= TP_long)
).fillna(False).astype(bool)

entries_short = (
    (current_median < previous_median) &
    (close_price < current_median)
    #(current_risk_ratio_short >= risk_ratio) &
    #(current_risk_ratio_short < 1)
).fillna(False).astype(bool)

exits_short = (
    (close_price >= SL_short) |
    (close_price <= TP_short)
).fillna(False).astype(bool)

pf = vbt.Portfolio.from_signals(
    close=close_price,
    entries=entries_long,
    exits=exits_long,
    short_entries=entries_short,
    short_exits=exits_short,
    size=fix_size,
    init_cash=10000,
    fees=0.001,
    freq='D'
)

trades = pf.trades.records_readable

trades['Entry Timestamp'] = pd.to_datetime(trades['Entry Timestamp'])
trades.set_index('Entry Timestamp', inplace=True)

trades['Current Median'] = current_median.loc[trades.index].values
trades['Previous Median'] = previous_median.loc[trades.index].values
trades['TP Long'] = TP_long.loc[trades.index].values
trades['SL Long'] = SL_long.loc[trades.index].values
trades['Current Risk Ratio Long'] = current_risk_ratio_long.loc[trades.index].values
trades['Current Risk Ratio Short'] = current_risk_ratio_short.loc[trades.index].values
trades['SL Short'] = SL_short.loc[trades.index].values
trades['TP Short'] = TP_short.loc[trades.index].values
trades['Upper Band'] = upper_band.loc[trades.index].values
trades['Lower Band'] = lower_band.loc[trades.index].values

trades.reset_index(inplace=True)

trades_file_path = f'data/{trading_instrument}_trades.xlsx'
trades.to_excel(trades_file_path, index=False)
print(f"Wykaz transakcji zapisany do {trades_file_path}")

diagnostic_data = pd.DataFrame({
    'Close Price': close_price,
    'Current Median': current_median,
    'Previous Median': previous_median,
    'Upper Band': upper_band,
    'Lower Band': lower_band,
    'SL Long': SL_long,
    'TP Long': TP_long,
    'SL Short': SL_short,
    'TP Short': TP_short,
    'Current Risk Ratio Long': current_risk_ratio_long,
    'Current Risk Ratio Short': current_risk_ratio_short,
    'Entries Long': entries_long,
    'Exits Long': exits_long,
    'Entries Short': entries_short,
    'Exits Short': exits_short
})

diagnostic_file_path = f'data/{trading_instrument}_diagnostic.xlsx'
diagnostic_data.to_excel(diagnostic_file_path, index=True)
print(f"Diagnostic file saved to {diagnostic_file_path}")

valid_data = merged_data[current_median > 0].dropna(subset=['Median_CloseAsk_10080min'])

filtered_current_median = valid_data['Median_CloseAsk_10080min']
filtered_upper_band = valid_data['Upper_Bollinger']
filtered_lower_band = valid_data['Lower_Bollinger']
filtered_close_price = valid_data['CloseAsk']

fig = pf.plot()
fig.update_layout(
    title=f'Portfolio Performance {pd.Timestamp.now()}',
    width=1400,
    height=2400
)

fig.add_scatter(
    x=filtered_current_median.index,
    y=filtered_current_median,
    mode='lines',
    name='Median',
    line=dict(dash='dash', color='blue')
)

fig.add_scatter(
    x=filtered_upper_band.index,
    y=filtered_upper_band,
    mode='lines',
    name='Upper Band',
    line=dict(dash='dot', color='green')
)

fig.add_scatter(
    x=filtered_lower_band.index,
    y=filtered_lower_band,
    mode='lines',
    name='Lower Band',
    line=dict(dash='dot', color='red')
)

fig.show()

print(pf.stats())
print(f"Total Return: {pf.total_return()}")
