import os
import json
import logging
from datetime import date

import boto3

from ingestion.stock_api_client import StockApiClient
from ingestion.ingestion_service import IngestionService
from shared.dynamodb_repository import DynamoDBRepository


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers:
        handler.setLevel(logging.INFO)


configure_logging()
logger = logging.getLogger(__name__)
ssm_client = boto3.client("ssm")


def get_massive_api_key() -> str:
    parameter_name = os.environ["MASSIVE_API_KEY_PARAMETER_NAME"]
    response = ssm_client.get_parameter(
        Name=parameter_name,
        WithDecryption=True,
    )
    return response["Parameter"]["Value"]


def get_requested_trading_date(event) -> date | None:
    if not event:
        return None

    trading_date = event.get("trading_date")
    if not trading_date:
        return None

    return date.fromisoformat(trading_date)

def lambda_handler(event, context):
    api_key = get_massive_api_key()
    requested_trading_date = get_requested_trading_date(event)
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    region = os.environ["AWS_REGION"]

    if not region:
        raise RuntimeError(
            "AWS_REGION environment variable is not set"
        )
    
    client = StockApiClient(api_key)
    service = IngestionService(client)
    repository = DynamoDBRepository(table_name, region)

    logger.info("Starting ingestion")

    try:
        winner = service.find_daily_top_mover(requested_trading_date)

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
