import os
import json
import logging
from decimal import Decimal
from shared.dynamodb_repository import DynamoDBRepository


def configure_logging() -> None:
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    for handler in root_logger.handlers:
        handler.setLevel(logging.INFO)


configure_logging()
logger = logging.getLogger(__name__)

CACHE_CONTROL_HEADER = "public, max-age=300"


def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    table_name = os.environ["DYNAMODB_TABLE_NAME"]
    region = os.environ["AWS_REGION"]
    repository = DynamoDBRepository(table_name, region=region)

    logger.info("Starting recent winners retrieval")

    try:
        items = repository.get_recent_winners()

        logger.info("Retrieval complete")

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": CACHE_CONTROL_HEADER,
            },
            "body": json.dumps(items, default=decimal_default),
        }
    except Exception:
        logger.exception("Recent winners retrieval failed")

        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
                "Cache-Control": "no-store",
            },
            "body": json.dumps({
                "message": "Failed to retrieve recent winners"
            }),
        }
