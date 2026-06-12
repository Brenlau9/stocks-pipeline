import os
import json
from dotenv import load_dotenv
import logging

from lambdas.ingestion.stock_api_client import StockApiClient
from lambdas.ingestion.ingestion_service import IngestionService
from lambdas.shared.dynamodb_repository import DynamoDBRepository


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def lambda_handler(event, context):
    api_key = os.getenv('MASSIVE_API_KEY')
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    region = os.getenv("AWS_REGION")

    if not region:
        raise RuntimeError(
            "AWS_REGION environment variable is not set"
        )
    
    client = StockApiClient(api_key)
    service = IngestionService(client)
    repository = DynamoDBRepository(table_name, region)

    logger.info("Starting ingestion")

    try:
        winner = service.find_daily_top_mover()

        # Need to save winner to DynamoDB
        logger.info(f"Winner: {winner}")

        repository.save_daily_winner(winner)

        logger.info("Ingestion complete")

        return {
            "statusCode": 200,
            "body": json.dumps(winner)
        }

    except Exception:
        logger.exception(
            "Ingestion job failed"
        )
        raise