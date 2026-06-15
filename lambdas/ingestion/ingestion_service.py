import logging
from datetime import date, timedelta

import holidays

from ingestion.constants import WATCHLIST
from ingestion.stock_api_client import StockApiClient

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, client: StockApiClient):
        self.client = client
        self.market_holidays = holidays.financial_holidays("NYSE")

    def calculate_percent_change(self, open_price, close_price):
        return ((close_price - open_price) / open_price) * 100

    def find_most_recent_trading_day(self) -> date:
        target_date = date.today() - timedelta(days=1)

        while not self.is_trading_day(target_date):
            logger.info(f"{target_date} is not a trading day. Trying previous day.")
            target_date -= timedelta(days=1)

        logger.info(f"Most recent trading day found: {target_date}")
        return target_date

    def is_trading_day(self, target_date: date) -> bool:
        if target_date.weekday() >= 5:
            return False

        return target_date not in self.market_holidays

    def find_daily_top_mover(self) -> dict:
        trading_day = self.find_most_recent_trading_day()

        best = 0
        winner = None

        logger.info(f"Starting daily mover calculation for {trading_day}")

        for ticker in WATCHLIST:
            data = self.client.get_open_close_data(ticker, trading_day)

            open_price = data["open"]
            close_price = data["close"]
            percent_change = self.calculate_percent_change(open_price, close_price)

            logger.info(f"{ticker} moved {percent_change:.2f}%")

            if abs(percent_change) > best:
                best = abs(percent_change)
                winner = {
                    "date": str(trading_day),
                    "ticker": ticker,
                    "percent_change": round(percent_change, 2),
                    "close_price": close_price,
                }
        if winner is None:
            raise RuntimeError("No winner found")

        logger.info(f"Top mover is {winner['ticker']}")

        return winner
