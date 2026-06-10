import os
from dotenv import load_dotenv
import logging

from stock_api_client import StockApiClient
from ingestion_service import IngestionService


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def lambda_handler(event, context):
    api_key = os.getenv('MASSIVE_API_KEY')

    client = StockApiClient(api_key)
    service = IngestionService(client)

    logger.info("Starting ingestion")

    try:
        winner = service.find_daily_top_mover()

        # Need to save winner to DynamoDB
        logger.info(f"Winner: {winner}")

        logger.info("Ingestion complete")

        return {
            "statusCode": 200,
            "body": winner
        }

    except Exception:
        logger.exception(
            "Ingestion job failed"
        )
        raise

if __name__ == "__main__":
    lambda_handler(None, None)