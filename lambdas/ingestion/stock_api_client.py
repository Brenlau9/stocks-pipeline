from datetime import date
import logging
import requests
import time

from ingestion.constants import (
    MAX_REQUEST_RETRIES,
    RATE_LIMIT_RETRY_SECONDS,
    REQUEST_CONNECT_TIMEOUT_SECONDS,
    REQUEST_INTERVAL_SECONDS,
    REQUEST_READ_TIMEOUT_SECONDS,
    RETRY_BACKOFF_BASE_SECONDS,
    RETRY_BACKOFF_MAX_SECONDS,
)

logger = logging.getLogger(__name__)


class StockApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.last_request_time = None

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
        attempt = 0

        while attempt < MAX_REQUEST_RETRIES:
            self.wait_for_request_interval()

            try:
                response = requests.get(
                    url,
                    params=params,
                    timeout=(
                        REQUEST_CONNECT_TIMEOUT_SECONDS,
                        REQUEST_READ_TIMEOUT_SECONDS,
                    ),
                )

                if response.status_code == 200:
                    return response

                if response.status_code == 429:
                    wait_time = self.get_retry_wait_time(response)
                    logger.warning(
                        f"Rate limited. Retrying in {wait_time:.1f} seconds."
                    )
                    time.sleep(wait_time)
                    continue

                if response.status_code >= 500:
                    self.sleep_before_retry(
                        attempt,
                        self.get_backoff_wait_time(attempt),
                        f"Massive API returned {response.status_code}",
                    )
                    attempt += 1
                    continue

                response.raise_for_status()

            except (
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
            ) as error:
                self.sleep_before_retry(
                    attempt,
                    self.get_backoff_wait_time(attempt),
                    f"Massive API request failed: {error}",
                )
                attempt += 1

        raise RuntimeError("Exceeded retry limit")

    def wait_for_request_interval(self) -> None:
        now = time.monotonic()

        if self.last_request_time is not None:
            wait_time = self.last_request_time + REQUEST_INTERVAL_SECONDS - now
            if wait_time > 0:
                logger.info(
                    f"Waiting {wait_time:.1f} seconds before next Massive API request."
                )
                time.sleep(wait_time)

        self.last_request_time = time.monotonic()

    def get_retry_wait_time(self, response: requests.Response) -> float:
        retry_after = response.headers.get("Retry-After")

        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                logger.warning(f"Invalid Retry-After header: {retry_after}")

        return RATE_LIMIT_RETRY_SECONDS

    def get_backoff_wait_time(self, attempt: int) -> float:
        return min(
            RETRY_BACKOFF_BASE_SECONDS * (2 ** attempt),
            RETRY_BACKOFF_MAX_SECONDS,
        )

    def sleep_before_retry(self, attempt: int, wait_time: float, reason: str) -> None:
        if attempt == MAX_REQUEST_RETRIES - 1:
            logger.error(f"{reason}. No retries remaining.")
            return

        logger.warning(
            f"{reason}. Retrying in {wait_time:.1f} seconds "
            f"(attempt {attempt + 2}/{MAX_REQUEST_RETRIES})."
        )
        time.sleep(wait_time)
