# Stocks Pipeline

Daily stock mover ingestion pipeline built with AWS Lambda, DynamoDB, EventBridge,
API Gateway, and Terraform.

The system wakes up the morning after each trading day, fetches open/close data
for a fixed watchlist, stores the stock with the largest absolute percentage
move, and exposes recent winners through an HTTP API.

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

Scheduled invocations do not pass a date and use the most recent completed
trading day before the current date.

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
cron(0 14 * * ? *)
```

AWS cron expressions are UTC. This schedule runs in the US morning after the
trading day, which avoids requesting same-day market data from Massive.

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

## Local Development Setup

Create and activate a virtual environment from the project root:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install --upgrade pip
```

Install runtime dependencies used by the Lambda code:

```bash
python3 -m pip install -r lambdas/ingestion/requirements.txt
```

The API Lambda currently has no third-party runtime dependencies. `boto3` is
available in the AWS Lambda Python runtime.

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

## Deploy Frontend

After Terraform creates the frontend S3 bucket, build and upload the static
frontend files:

```bash
./scripts/deploy_frontend.sh
```

The script builds `frontend/dist` and syncs its contents to the S3 website
bucket from Terraform output. It uploads `index.html` at the bucket root and
uses `--delete` so removed build assets do not stay behind in S3.

## Useful Outputs

After deploy:

```bash
terraform -chdir=terraform output
```

Important outputs:

- `ingestion_lambda_name`
- `api_lambda_name`
- `movers_endpoint_url`
- `frontend_bucket_name`
- `frontend_website_url`
- `dynamodb_table_name`

## Manual Ingestion Invoke

Invoke the ingestion Lambda for its default previous-trading-day behavior:

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

## Integration Smoke Test

Run a lightweight deployed-system check:

```bash
./scripts/integration_smoke_test.sh
```

This verifies Terraform outputs, `GET /movers`, the DynamoDB-backed response
shape, and the S3 frontend website. To also invoke the ingestion Lambda for a
completed historical trading day and verify that record through the API:

```bash
./scripts/integration_smoke_test.sh --ingest 2026-06-12
```

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

- The scheduled job looks for the most recent completed trading day before the
  current date so it does not request same-day Massive data. Use the
  `trading_date` payload with a completed historical trading day for manual
  testing.

- Terraform state is currently local unless you configure a remote backend.
  Do not commit `terraform.tfstate`, `terraform.tfvars`, or `.env` files.
