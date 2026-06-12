import logging
from decimal import Decimal
from typing import Any, List

import boto3

logger = logging.getLogger(__name__)

class DynamoDBRepository:
    def __init__(self, table_name: str, region: str):
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
    
    def get_recent_winners(self) -> List[dict]:
        response = self.table.scan()

        items = response.get("Items", [])

        items.sort(
            key=lambda x: x["date"],
            reverse=True
        )

        logger.info(f"Retrieved recent winners from DynamoDB: {items[:7]}")

        return items[:7]