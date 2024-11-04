import pandas as pd
import vectorbt as vbt
import yaml
import datetime
import plotly.io as pio

pio.renderers.default = 'browser'

# Wczytanie ustawień z pliku system_settings.yml
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

days = settings.get('days')
trading_instrument = settings.get('trading_instrument')
risk_ratio = settings.get('risk_ratio')
stop_loss_percentage = settings.get('stop_loss_percentage')

# Wczytanie pliku danych dla określonego instrumentu
file_path = f'data/{trading_instrument}_merged_data.xlsx'
merged_data = pd.read_excel(file_path)

# Konwersja kolumny 'Datetime' na format datetime i ustawienie jako indeks
merged_data['Datetime'] = pd.to_datetime(merged_data['Datetime'])
merged_data.set_index('Datetime', inplace=True)

# Ekstrakcja kolumn i konwersja do odpowiednich typów
close_price = merged_data['Close_x'].astype(float).fillna(0)
max_price = merged_data['High_x'].astype(float).fillna(0)
low_price = merged_data['Low_x'].astype(float).fillna(0)
current_median = merged_data['current_median'].astype(float).fillna(0)
previous_median = merged_data['previous_median'].astype(float).fillna(0)
upper_band = merged_data['Upper Band'].astype(float).fillna(0)
lower_band = merged_data['Lower Band'].astype(float).fillna(0)
current_risk_ratio = round((current_median / close_price), 4).fillna(0)

# Definiowanie warunków wejścia i wyjścia dla pozycji long i short
entries_long = (
    (current_median > previous_median) &
    (max_price > current_median) &
    (current_risk_ratio >= risk_ratio) &
    (current_risk_ratio <= 1)
).fillna(False).astype(bool)

SL_long = round(current_median - (stop_loss_percentage * (current_median - lower_band)), 2)
TP_long = upper_band

exits_long = (
    (current_median <= previous_median) |
    (low_price <= SL_long) |
    (max_price >= TP_long)
).fillna(False).astype(bool)

entries_short = (
    (current_median < previous_median) &
    (low_price < current_median) &
    (current_risk_ratio >= risk_ratio) &
    (current_risk_ratio <= 1)
).fillna(False).astype(bool)

SL_short = round(current_median + (stop_loss_percentage * (upper_band - current_median)), 2)
TP_short = lower_band

exits_short = (
    (current_median >= previous_median) |
    (max_price >= SL_short) |
    (low_price <= TP_short)
).fillna(False).astype(bool)

# Dodanie kolumn diagnostycznych do DataFrame
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

# Zapisanie danych diagnostycznych do pliku Excel
diagnostic_file_path = f'data/{trading_instrument}_diagnostics.xlsx'
merged_data.to_excel(diagnostic_file_path, index=True)

print(f"Informacje diagnostyczne zapisane do {diagnostic_file_path}")

# Tworzenie portfela bez dynamicznej wielkości pozycji
pf = vbt.Portfolio.from_signals(
    close=close_price,
    entries=entries_long,
    exits=exits_long,
    short_entries=entries_short,
    short_exits=exits_short,
    init_cash=10000,
    fees=0.001,
    freq='D'
)

# Wyciągnięcie informacji o transakcjach
trades = pf.trades.records_readable

# Zapisanie wykazu transakcji do pliku Excel
trades_file_path = f'data/{trading_instrument}_trades.xlsx'
trades.to_excel(trades_file_path, index=False)

print(f"Wykaz transakcji zapisany do {trades_file_path}")

# Generowanie wykresu z transakcjami
fig = pf.plot()
fig.update_layout(title='Portfolio Performance with Long and Short Transactions')

# Dodanie punktów wejścia i wyjścia dla transakcji Long i Short na wykresie
long_entries_idx = merged_data.index[entries_long]
long_exits_idx = merged_data.index[exits_long]
short_entries_idx = merged_data.index[entries_short]
short_exits_idx = merged_data.index[exits_short]

fig.add_scatter(x=long_entries_idx, y=close_price[entries_long], mode='markers', name='Long Entry', marker=dict(color='green', symbol='triangle-up'))
fig.add_scatter(x=long_exits_idx, y=close_price[exits_long], mode='markers', name='Long Exit', marker=dict(color='darkgreen', symbol='triangle-down'))
fig.add_scatter(x=short_entries_idx, y=close_price[entries_short], mode='markers', name='Short Entry', marker=dict(color='red', symbol='triangle-up'))
fig.add_scatter(x=short_exits_idx, y=close_price[exits_short], mode='markers', name='Short Exit', marker=dict(color='darkred', symbol='triangle-down'))

fig.show()

# Wyświetlenie statystyk portfela
print(pf.stats())
print(f"Total Return: {pf.total_return()}")
