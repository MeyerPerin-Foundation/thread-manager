import requests
import app_config

class AlphaVantageContent:

    def __init__(self, api_key):
        self.api_key = app_config.ALPHA_VANTAGE_API_KEY

    def get_daily_close(self, symbol, start_date = None, end_date = None):
        if start_date and end_date:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}&outputsize=full"
            response = requests.get(url)
            data = response.json()
            time_series = data["Time Series (Daily)"]
            # get only the dates in the range and only the close
            filtered_data = {date: time_series[date]["4. close"] for date in time_series if start_date <= date <= end_date}
            return filtered_data
        elif start_date:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}&outputsize=full"
            response = requests.get(url)
            data = response.json()
            time_series = data["Time Series (Daily)"]
            # get only the dates in the range and only the close
            filtered_data = {date: time_series[date]["4. close"] for date in time_series if start_date <= date}
            return filtered_data
        else:
            url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={symbol}&apikey={self.api_key}"
            response = requests.get(url)
            data = response.json()
            time_series = data["Time Series (Daily)"]
            return time_series

if __name__ == "__main__":
    a = AlphaVantageContent(app_config.ALPHA_VANTAGE_API_KEY)
    print(a.get_daily_close("AAPL", start_date="2023-01-01", end_date="2023-01-31"))