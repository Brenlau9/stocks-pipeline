import json

from lambdas.ingestion.handler import lambda_handler as ingestion_handler
from lambdas.api.handler import lambda_handler as api_handler


def run_ingestion():
    print("\n=== Running Ingestion Lambda ===\n")

    response = ingestion_handler(
        event={},
        context=None
    )

    print(
        json.dumps(
            response,
            indent=2
        )
    )


def run_api():
    print("\n=== Running Retrieval Lambda ===\n")

    response = api_handler(
        event={},
        context=None
    )

    print(
        json.dumps(
            response,
            indent=2
        )
    )


def main():
    run_ingestion()
    run_api()


if __name__ == "__main__":
    main()