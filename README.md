# Stocks Pipeline

Daily stock mover ingestion pipeline built with AWS Lambda, DynamoDB, EventBridge,
API Gateway, and Terraform.

The system wakes up after market close, fetches open/close data for a fixed
watchlist, stores the stock with the largest absolute percentage move, and
exposes recent winners through an HTTP API.

## Architecture

```text
EventBridge schedule
        |
        v
Ingestion Lambda -----> Massive API
        |
        v
DynamoDB daily-stock-movers
        ^
        |
API Lambda <----- API Gateway GET /movers
```

## Components

### Ingestion Lambda

Path: `lambdas/ingestion`

The ingestion Lambda:

- Reads the Massive API key from SSM Parameter Store at runtime.
- Uses the NYSE calendar from the `holidays` package to find the trading day.
- Fetches open/close data for the configured watchlist.
- Spaces Massive API calls 15 seconds apart.
- Retries timeouts, connection errors, and 5xx responses with backoff.
- Waits on 429 rate-limit responses before retrying.
- Stores the winning stock in DynamoDB.

The watchlist is configured in:

```text
lambdas/ingestion/constants.py
```

Manual invocations can pass a historical trading date:

```json
{"trading_date":"2026-06-12"}
```

Scheduled invocations do not pass a date and use the most recent trading day
based on the current date.

### API Lambda

Path: `lambdas/api`

The API Lambda reads from DynamoDB and returns the most recent seven winning
stock records as JSON.

### Shared Code

Path: `lambdas/shared`

Shared DynamoDB repository code used by both Lambdas.

### DynamoDB

Terraform file:

```text
terraform/dynamodb.tf
```

The table uses `date` as the partition key and stores one winning stock per
trading date.

### EventBridge

Terraform file:

```text
terraform/eventbridge.tf
```

Runs the ingestion Lambda once per day:

```text
cron(0 22 * * ? *)
```

AWS cron expressions are UTC. This schedule is intended to run after US market
close with some buffer.

### API Gateway

Terraform file:

```text
terraform/api_gateway.tf
```

Creates an HTTP API endpoint:

```text
GET /movers
```

This route invokes the API Lambda and returns the latest seven records from
DynamoDB.

## Prerequisites

- AWS CLI configured for the target account.
- Terraform installed.
- Python 3 available locally.
- Massive API key.

The Terraform defaults deploy to:

```text
us-west-2
```

## Secret Setup

The Massive API key is stored in SSM Parameter Store as a `SecureString`.
Create it before applying Terraform:

```bash
aws ssm put-parameter \
  --name /stocks-pipeline/massive-api-key \
  --type SecureString \
  --value 'YOUR_MASSIVE_API_KEY' \
  --region us-west-2
```

If the parameter already exists, use `--overwrite`:

```bash
aws ssm put-parameter \
  --name /stocks-pipeline/massive-api-key \
  --type SecureString \
  --value 'YOUR_MASSIVE_API_KEY' \
  --overwrite \
  --region us-west-2
```

Terraform stores only the parameter name and ARN, not the secret value.

## Packaging Lambdas

Terraform packages Lambdas from `terraform/build`, so rebuild the package
directories before applying infrastructure changes that include Lambda code.

From the project root:

```bash
./scripts/package_lambdas.sh
```

This script:

- Clears and rebuilds `terraform/build/ingestion_package`.
- Clears and rebuilds `terraform/build/api_package`.
- Copies Lambda source code and shared code.
- Installs Python dependencies for Lambda Python 3.12/Linux.
- Removes stale Lambda zip files so Terraform recreates them.

## Deploy

From the project root:

```bash
./scripts/package_lambdas.sh
terraform -chdir=terraform init
terraform -chdir=terraform apply
```

Review the Terraform plan, then approve it.

## Useful Outputs

After deploy:

```bash
terraform -chdir=terraform output
```

Important outputs:

- `ingestion_lambda_name`
- `api_lambda_name`
- `movers_endpoint_url`
- `dynamodb_table_name`

## Manual Ingestion Invoke

Invoke the ingestion Lambda for its default trading-day behavior:

```bash
aws lambda invoke \
  --function-name "$(terraform -chdir=terraform output -raw ingestion_lambda_name)" \
  --region us-west-2 \
  terraform/response.json
```

Invoke for a specific historical trading day:

```bash
aws lambda invoke \
  --function-name "$(terraform -chdir=terraform output -raw ingestion_lambda_name)" \
  --region us-west-2 \
  --cli-binary-format raw-in-base64-out \
  --payload '{"trading_date":"2026-06-12"}' \
  terraform/response.json
```

View the Lambda response:

```bash
cat terraform/response.json
```

## Test the API

After Terraform creates API Gateway:

```bash
curl "$(terraform -chdir=terraform output -raw movers_endpoint_url)"
```

Expected response shape:

```json
[
  {
    "date": "2026-06-12",
    "ticker": "AAPL",
    "percent_change": 1.23,
    "close_price": 201.45
  }
]
```

The API returns up to seven most recent records.

## Local Validation

Run Python syntax checks:

```bash
python3 -m compileall lambdas
```

Check Terraform formatting:

```bash
terraform -chdir=terraform fmt -check -recursive
```

Validate Terraform:

```bash
terraform -chdir=terraform validate
```

## Notes

- If you manually invoke before market close, today's open/close endpoint may
  require a paid Massive tier. Use the `trading_date` payload with a completed
  historical trading day for manual testing.

- Terraform state is currently local unless you configure a remote backend.
  Do not commit `terraform.tfstate`, `terraform.tfvars`, or `.env` files.
