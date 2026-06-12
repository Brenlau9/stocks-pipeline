import os
import json
from dotenv import load_dotenv
import logging
from decimal import Decimal
from lambdas.shared.dynamodb_repository import DynamoDBRepository

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def lambda_handler(event, context):
    table_name = os.getenv('DYNAMODB_TABLE_NAME')
    region = os.getenv('AWS_REGION')
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
            },
            "body": json.dumps({
                "message": "Failed to retrieve recent winners"
            }),
        }
