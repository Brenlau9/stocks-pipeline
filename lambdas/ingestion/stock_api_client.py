from datetime import datetime, date, timedelta
import logging
import requests
import time

logger = logging.getLogger(__name__)

class StockApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_open_close_data(self, ticker: str, target_date: date) -> dict:
        if not self.api_key:
            raise RuntimeError("MASSIVE_API_KEY environment variable is not set")

        params = {"apiKey": self.api_key}
        url = f"https://api.massive.com/v1/open-close/{ticker}/{target_date}"

        logger.info(f"Fetching {ticker}")

        response = self.make_request(url, params)

        if response.status_code != 200:
            logger.error(
                f"Failed to fetch {ticker}. Status={response.status_code}"
            )

        data = response.json()

        logger.info(
            f"Fetched {ticker} successfully. Open price is {data['open']}. Close price is {data['close']}"
        )
        return data

    def make_request(self, url: str, params: dict[str, str]) -> requests.Response:
        max_retries = 3

        for attempt in range(max_retries):
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                return response

            if response.status_code == 429:
                wait_time = 60
                logger.warning(
                    f"Rate limited. Retrying"
                )
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
        
        raise RuntimeError("Exceeded retry limit")