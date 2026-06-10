from stock_api_client import StockApiClient

from datetime import datetime, date, timedelta
import time

class IngestionService:
    def __init__(self, client: StockApiClient):
        self.client = client

    def calculate_percent_change(self, open_price, close_price):
        return ((close_price - open_price) / open_price) * 100
    
    def find_daily_top_mover(self) -> str:
        yesterday = date.today() - timedelta(days=1)
        WATCHLIST = ["AAPL","MSFT","GOOGL","AMZN","TSLA","NVDA"]

        best = 0
        winner = ""

        for ticker in WATCHLIST:
            response = self.client.get_open_close_data(ticker, yesterday)
            print(response.json())
            data = response.json()
            open_price = data['open']
            close_price = data['close']
            percent_change = self.calculate_percent_change(open_price, close_price)
            
            if abs(percent_change) > best:
                winner = ticker
            time.sleep(12)
        
        return winner