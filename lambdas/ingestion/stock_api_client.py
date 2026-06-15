from datetime import date
import logging
import requests
import time

from ingestion.constants import (
    MAX_REQUESTS_PER_MINUTE,
    RATE_LIMIT_SAFETY_BUFFER_SECONDS,
    RATE_LIMIT_WINDOW_SECONDS,
)

logger = logging.getLogger(__name__)


class StockApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.request_timestamps = []

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
            self.wait_for_rate_limit()
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                return response

            if response.status_code == 429:
                wait_time = self.get_retry_wait_time(response)
                logger.warning(
                    f"Rate limited. Retrying in {wait_time:.1f} seconds."
                )
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
        
        raise RuntimeError("Exceeded retry limit")

    def wait_for_rate_limit(self) -> None:
        now = time.monotonic()
        window_start = now - RATE_LIMIT_WINDOW_SECONDS
        self.request_timestamps = [
            timestamp
            for timestamp in self.request_timestamps
            if timestamp > window_start
        ]

        wait_time = 0

        if len(self.request_timestamps) >= MAX_REQUESTS_PER_MINUTE:
            oldest_request = self.request_timestamps[0]
            wait_time = max(
                wait_time,
                oldest_request
                + RATE_LIMIT_WINDOW_SECONDS
                - now
                + RATE_LIMIT_SAFETY_BUFFER_SECONDS,
            )

        if self.request_timestamps:
            min_interval = (
                RATE_LIMIT_WINDOW_SECONDS / MAX_REQUESTS_PER_MINUTE
                + RATE_LIMIT_SAFETY_BUFFER_SECONDS
            )
            wait_time = max(wait_time, self.request_timestamps[-1] + min_interval - now)

        if wait_time > 0:
            logger.info(
                f"Waiting {wait_time:.1f} seconds before next Massive API request."
            )
            time.sleep(wait_time)

        self.request_timestamps.append(time.monotonic())

    def get_retry_wait_time(self, response: requests.Response) -> float:
        retry_after = response.headers.get("Retry-After")

        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                logger.warning(f"Invalid Retry-After header: {retry_after}")

        return RATE_LIMIT_WINDOW_SECONDS
