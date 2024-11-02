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

# Ustal zakres dat
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=days)  # na przykład ostatnie 90 dni

# Pobranie danych godzinowych za pomocą vectorbt
hourly_data = vbt.YFData.download(
    trading_instrument,
    missing_index="drop",
    start=start_date,
    end=end_date,
    interval="1h"
).get()

# Przekształcenie danych godzinowych na dane tygodniowe
weekly_data = hourly_data.resample('W').agg({
    'Open': 'first',    # Pierwsza cena w tygodniu
    'High': 'max',      # Maksymalna cena w tygodniu
    'Low': 'min',       # Minimalna cena w tygodniu
    'Close': 'last',    # Ostatnia cena w tygodniu
    'Volume': 'sum'     # Suma wolumenu dla tygodnia
}).dropna()

weekly_data['Rolling Median'] = weekly_data['Close'].rolling(window=median_periods).median().round(2)
weekly_data['Rolling Std Dev'] = weekly_data['Close'].rolling(window=median_periods).std()
weekly_data['Upper Band'] = (weekly_data['Rolling Median'] + band_width_factor * weekly_data['Rolling Std Dev']).round(2)
weekly_data['Lower Band'] = (weekly_data['Rolling Median'] - band_width_factor * weekly_data['Rolling Std Dev']).round(2)

# Usuń kolumnę Rolling Std Dev, jeśli nie jest potrzebna
weekly_data = weekly_data.drop(columns=['Rolling Std Dev'])

# Zapisz dane tygodniowe do pliku CSV
weekly_filename = "data/weekly_data.csv"
weekly_data.to_csv(weekly_filename, index=True)
