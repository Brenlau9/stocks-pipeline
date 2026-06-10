from datetime import datetime, date, timedelta
import requests
import time

class StockApiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key

    def get_open_close_data(self, ticker: str, target_date: date) -> dict:
        if not self.api_key:
            raise RuntimeError("MASSIVE_API_KEY environment variable is not set")
    
        params = {"apiKey": self.api_key}
        url = f"https://api.massive.com/v1/open-close/{ticker}/{target_date}"
        response = self.make_request(url, params)

        if response.status_code != 200:
            print(f"Error {response.status_code}: {response.text}")
        return response

    def make_request(self, url: str, params: dict[str, str]) -> dict:
        max_retries = 3

        for attempt in range(max_retries):
            response = requests.get(url, params=params, timeout=20)
            
            if response.status_code == 200:
                return response

            if response.status_code == 429:
                wait_time = 60
                print(f"Rate Limited. Waiting {wait_time} seconds...")
                time.sleep(wait_time)
                continue
            
            response.raise_for_status()
        
        raise RuntimeError("Exceeded retry limit")