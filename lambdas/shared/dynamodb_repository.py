import logging
from datetime import date, timedelta
from decimal import Decimal
from typing import Any

import boto3

logger = logging.getLogger(__name__)

RECENT_WINNERS_LIMIT = 7
RECENT_WINNERS_LOOKBACK_DAYS = 30

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
    
    def get_winner_by_date(self, trading_date: date) -> dict[str, Any] | None:
        response = self.table.get_item(
            Key={
                "date": trading_date.isoformat(),
            }
        )

        return response.get("Item")

    def get_recent_winners(self) -> list[dict[str, Any]]:
        winners = []
        target_date = date.today()

        for _ in range(RECENT_WINNERS_LOOKBACK_DAYS):
            item = self.get_winner_by_date(target_date)
            if item:
                winners.append(item)

            if len(winners) == RECENT_WINNERS_LIMIT:
                break

            target_date -= timedelta(days=1)

        logger.info(f"Retrieved recent winners from DynamoDB: {winners}")

        return winners
