from lambdas.ingestion.stock_api_client import StockApiClient
import logging
from datetime import datetime, date, timedelta
import time
from lambdas.ingestion.constants import WATCHLIST

logger = logging.getLogger(__name__)

class IngestionService:
    def __init__(self, client: StockApiClient):
        self.client = client

    def calculate_percent_change(self, open_price, close_price):
        return ((close_price - open_price) / open_price) * 100
    
    def find_daily_top_mover(self) -> dict:
        yesterday = date.today() - timedelta(days=1)

        best = 0
        winner = None

        logger.info("Starting daily mover calculation")

        for ticker in WATCHLIST:
            data = self.client.get_open_close_data(ticker, yesterday)
            open_price = data['open']
            close_price = data['close']
            percent_change = self.calculate_percent_change(open_price, close_price)
            
            logger.info(
                f"{ticker} moved {percent_change:.2f}%"
            )

            if abs(percent_change) > best:
                best = abs(percent_change)
                winner = {
                    "date": str(yesterday),
                    "ticker": ticker,
                    "percent_change": round(percent_change, 2),
                    "close_price": close_price,
                }
            time.sleep(12)
        
        if winner is None:
            raise RuntimeError("No winner found")
        
        logger.info(
            f"Top mover is {winner['ticker']}"
        )

        return winner