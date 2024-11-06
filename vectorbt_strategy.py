import pandas as pd
import vectorbt as vbt
import yaml
import plotly.io as pio

pio.renderers.default = 'browser'

# Wczytanie ustawień z pliku system_settings.yml
with open('system_settings.yml', 'r') as file:
    settings = yaml.safe_load(file)

days = settings.get('days')
trading_instrument = settings.get('trading_instrument')
risk_ratio = settings.get('risk_ratio')
stop_loss_percentage = settings.get('stop_loss_percentage')
risk_level = settings.get('risk_level')  # Dodane dla poziomu ryzyka

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

# Funkcja obliczająca wielkość pozycji dla pozycji długiej
def calculate_position_size_long(
    current_median,
    close_price,
    stop_loss_percentage,
    lower_band,
    available_capital,
    risk_ratio
):
    SL_p = stop_loss_percentage * (current_median - lower_band)
    SL_long = current_median - SL_p
    max_loss = close_price - SL_long
    risk_value = available_capital * risk_ratio
    position_size = risk_value / max_loss
    return position_size

# Funkcja obliczająca wielkość pozycji dla pozycji krótkiej
def calculate_position_size_short(
    current_median,
    close_price,
    stop_loss_percentage,
    upper_band,
    available_capital,
    risk_level
):
    # Obliczanie SL dla pozycji krótkiej zgodnie z przedstawioną metodologią
    SL_p = stop_loss_percentage * (upper_band - current_median)
    SL_short = current_median + SL_p
    max_loss = SL_short - close_price
    risk_value = available_capital * risk_level
    position_size = risk_value / max_loss
    return position_size

# Przygotowanie dostępnego kapitału
initial_capital = 10000
available_capital = initial_capital
position_sizes_long = []
position_sizes_short = []

# Iteracja przez dane w celu obliczenia dynamicznej wielkości pozycji dla każdego punktu czasowego
for i in range(len(merged_data)):
    current_median_i = current_median.iloc[i]
    close_price_i = close_price.iloc[i]
    lower_band_i = lower_band.iloc[i]
    upper_band_i = upper_band.iloc[i]

    # Obliczenie wielkości pozycji long
    position_size_long = calculate_position_size_long(
        current_median=current_median_i,
        close_price=close_price_i,
        stop_loss_percentage=stop_loss_percentage,
        lower_band=lower_band_i,
        available_capital=available_capital,
        risk_ratio=risk_ratio
    )
    position_sizes_long.append(position_size_long)

    # Obliczenie wielkości pozycji short
    position_size_short = calculate_position_size_short(
        current_median=current_median_i,
        close_price=close_price_i,
        stop_loss_percentage=stop_loss_percentage,
        upper_band=upper_band_i,
        available_capital=available_capital,
        risk_level=risk_level
    )
    position_sizes_short.append(position_size_short)

# Tworzenie serii z wielkością pozycji dla każdej transakcji long i short
position_sizes_long_series = pd.Series(position_sizes_long, index=merged_data.index)
position_sizes_short_series = pd.Series(position_sizes_short, index=merged_data.index)

# Tworzenie portfela z dynamiczną wielkością pozycji dla long i short
pf = vbt.Portfolio.from_signals(
    close=close_price,
    entries=entries_long,
    exits=exits_long,
    short_entries=entries_short,
    short_exits=exits_short,
    size=pd.concat([position_sizes_long_series, position_sizes_short_series], axis=1).max(axis=1),
    init_cash=initial_capital,
    fees=0.001,
    freq='D'
)

# Wyciągnięcie informacji o transakcjach
trades = pf.trades.records_readable

# Konwersja 'Entry Timestamp' na format datetime i ustawienie jako indeks
trades['Entry Timestamp'] = pd.to_datetime(trades['Entry Timestamp'])
trades.set_index('Entry Timestamp', inplace=True)

# Dodanie kolumny z wielkością pozycji do DataFrame trades
# Dopasowanie wielkości pozycji do każdej transakcji na podstawie 'Entry Timestamp'
trades['Position Size Long'] = position_sizes_long_series.loc[trades.index].values
trades['Position Size Short'] = position_sizes_short_series.loc[trades.index].values

# Resetowanie indeksu, aby 'Entry Timestamp' był kolumną
trades.reset_index(inplace=True)

# Zapisanie danych diagnostycznych do pliku Excel
diagnostic_file_path = f'data/{trading_instrument}_diagnostics.xlsx'
merged_data.to_excel(diagnostic_file_path, index=True)
print(f"Informacje diagnostyczne zapisane do {diagnostic_file_path}")

# Zapisanie wykazu transakcji do pliku Excel z kolumnami 'Position Size Long' i 'Position Size Short'
trades_file_path = f'data/{trading_instrument}_trades.xlsx'
trades.to_excel(trades_file_path, index=False)
print(f"Wykaz transakcji zapisany do {trades_file_path}")

# Generowanie wykresu z transakcjami
fig = pf.plot()
fig.update_layout(title='Portfolio Performance with Long and Short Transactions')

fig.show()

# Wyświetlenie statystyk portfela
print(pf.stats())
print(f"Total Return: {pf.total_return()}")
