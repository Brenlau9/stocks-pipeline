import logging
from datetime import date, timedelta

import requests

from ingestion.constants import WATCHLIST, MAX_TRADING_DAY_LOOKBACK
from ingestion.stock_api_client import StockApiClient

logger = logging.getLogger(__name__)


class IngestionService:
    def __init__(self, client: StockApiClient):
        self.client = client

    def calculate_percent_change(self, open_price, close_price):
        return ((close_price - open_price) / open_price) * 100

    def find_most_recent_trading_day(self) -> tuple[date, dict]:
        target_date = date.today() - timedelta(days=1)
        reference_ticker = WATCHLIST[0]

        logger.info(
            f"Finding most recent trading day using {reference_ticker} as reference ticker"
        )

        for _ in range(MAX_TRADING_DAY_LOOKBACK):
            try:
                reference_data = self.client.get_open_close_data(
                    reference_ticker,
                    target_date,
                )

                logger.info(f"Most recent trading day found: {target_date}")
                return target_date, reference_data

            except requests.HTTPError:
                logger.warning(
                    f"No market data found for {target_date}. Trying previous day."
                )
                target_date -= timedelta(days=1)

        raise RuntimeError("Unable to find a recent trading day")

    def find_daily_top_mover(self) -> dict:
        trading_day, reference_data = self.find_most_recent_trading_day()

        best = 0
        winner = None

        logger.info(f"Starting daily mover calculation for {trading_day}")

        for index, ticker in enumerate(WATCHLIST):
            if index == 0:
                data = reference_data
            else:
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
