import logging
from decimal import Decimal
from typing import Any

import os
import boto3

logger = logging.getLogger(__name__)

class DynamoDBRepository:
    def __init__(self, table_name: str):
        region = os.getenv("AWS_REGION", "us-west-2")

        if not region:
            raise RuntimeError(
                "AWS_REGION environment variable is not set"
            )
    
        self.table_name = table_name
        
        self.table = boto3.resource(
            "dynamodb", 
            region_name=region,
        ).Table(table_name)

    def save_daily_winner(self, winner: dict[str, Any]) -> None:
        item = {
            "date": winner["date"],
            "ticker": winner["ticker"],
            "percent_change": Decimal(str(winner["percent_change"])),
            "close_price": Decimal(str(winner["close_price"])),
        }

        logger.info(f"Saving winner to DynamoDB: {item}")

        self.table.put_item(Item=item)

        logger.info("Winner saved successfully")