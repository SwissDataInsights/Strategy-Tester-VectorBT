import pandas as pd
import vectorbt as vbt
from openbb import obb

# Załóżenia
initial_cash = 10000
fee = 0.001  # Opłata transakcyjna 0.1%

# Pobranie danych minutowych dla Swiss Re
dane = obb.equity.price.historical(
    symbol='SREN.SW',
    interval='1m',  # Interwał minutowy
    start_date='2024-01-01',  # Data początkowa
    end_date='2024-10-31',    # Data końcowa
    provider='yfinance'       # Dostawca danych
)

# Konwersja danych do formatu pandas DataFrame
data_list = [
    {
        'date': item.date,
        'open': item.open,
        'high': item.high,
        'low': item.low,
        'close': item.close,
        'volume': item.volume
    }
    for item in dane.results
]

df = pd.DataFrame(data_list)
prices = df.set_index('date')['close']

# Obliczenia mediany i zmiennych
prices_daily = prices.resample('D').last()  # Próbkowanie danych minutowych do dziennego interwału
window_size = 5  # Mediana tygodniowa (5 dni roboczych)
current_median = prices_daily.rolling(window=window_size).median()
current_median = current_median.reindex(prices.index, method='ffill')  # Przypisanie mediany do minutowego interwału
previous_median = current_median.shift(1)

# Obliczanie górnej i dolnej bandy zgodnie z medianą
upper_band = current_median + 1.5 * current_median.rolling(window=window_size).std()
lower_band = current_median - 1.5 * current_median.rolling(window=window_size).std()
upper_band = upper_band.reindex(prices.index, method='ffill')
lower_band = lower_band.reindex(prices.index, method='ffill')

# Definicje warunków otwarcia pozycji
entries_long = (current_median > previous_median) & (prices > current_median)
exits_long = (current_median <= previous_median) | (prices <= lower_band) | (prices <= (current_median - 0.3 * (current_median - lower_band)))

# Definicje warunków otwarcia pozycji Short
entries_short = (current_median < previous_median) & (prices < current_median)
exits_short = (current_median >= previous_median) | (prices >= upper_band) | (prices >= (current_median + 0.3 * (upper_band - current_median)))

# Backtestowanie strategii dla pozycji Long
pf_long = vbt.Portfolio.from_signals(
    close=prices,
    entries=entries_long,
    exits=exits_long,
    init_cash=initial_cash,
    fees=fee,
    freq='1min'  # Ustawienie częstotliwości na 1 minutę
)

# Backtestowanie strategii dla pozycji Short
pf_short = vbt.Portfolio.from_signals(
    close=prices,
    entries=entries_short,
    exits=exits_short,
    init_cash=initial_cash,
    fees=fee,
    freq='1min'  # Ustawienie częstotliwości na 1 minutę
)

# Statystyki
print("Wyniki dla pozycji Long:")
print(pf_long.stats())
print("\nWyniki dla pozycji Short:")
print(pf_short.stats())

# Wizualizacja wyników
pf_long.plot().show()
pf_short.plot().show()
