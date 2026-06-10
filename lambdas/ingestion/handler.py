import os
from dotenv import load_dotenv
import logging
from datetime import datetime, date, timedelta
import time

import boto3
import requests

from stock_api_client import StockApiClient
from ingestion_service import IngestionService

load_dotenv()

def lambda_handler():
    api_key = os.getenv('MASSIVE_API_KEY')

    client = StockApiClient(api_key)
    service = IngestionService(client)

    winner = service.find_daily_top_mover()

    print(winner)

if __name__ == "__main__":
    lambda_handler()