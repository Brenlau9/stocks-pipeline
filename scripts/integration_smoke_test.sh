#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TERRAFORM_DIR="${ROOT_DIR}/terraform"
AWS_REGION="${AWS_REGION:-us-west-2}"
RUN_INGESTION=false
TRADING_DATE=""

usage() {
  cat <<'EOF'
Usage:
  ./scripts/integration_smoke_test.sh
  ./scripts/integration_smoke_test.sh --ingest YYYY-MM-DD

Checks deployed Terraform outputs, API Gateway, DynamoDB-backed API data, and
the S3 static frontend. With --ingest, invokes the ingestion Lambda for a
completed historical trading day and verifies that date appears in GET /movers.
EOF
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

terraform_output() {
  terraform -chdir="${TERRAFORM_DIR}" output -raw "$1"
}

pass() {
  echo "PASS: $1"
}

fail() {
  echo "FAIL: $1" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ingest)
      RUN_INGESTION=true
      TRADING_DATE="${2:-}"
      if [[ -z "${TRADING_DATE}" ]]; then
        fail "--ingest requires a YYYY-MM-DD date"
      fi
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage
      fail "Unknown argument: $1"
      ;;
  esac
done

require_command aws
require_command curl
require_command python3
require_command terraform

API_URL="$(terraform_output movers_endpoint_url)"
FRONTEND_URL="$(terraform_output frontend_website_url)"
INGESTION_LAMBDA_NAME="$(terraform_output ingestion_lambda_name)"

[[ -n "${API_URL}" ]] || fail "movers_endpoint_url Terraform output is empty"
[[ -n "${FRONTEND_URL}" ]] || fail "frontend_website_url Terraform output is empty"
[[ -n "${INGESTION_LAMBDA_NAME}" ]] || fail "ingestion_lambda_name Terraform output is empty"
pass "Terraform outputs are available"

if [[ "${RUN_INGESTION}" == "true" ]]; then
  echo "Invoking ingestion Lambda for ${TRADING_DATE}..."
  LAMBDA_RESPONSE_FILE="$(mktemp)"
  LAMBDA_PAYLOAD="{\"trading_date\":\"${TRADING_DATE}\"}"

  INVOKE_OUTPUT="$(
    aws lambda invoke \
      --function-name "${INGESTION_LAMBDA_NAME}" \
      --region "${AWS_REGION}" \
      --cli-binary-format raw-in-base64-out \
      --cli-read-timeout 300 \
      --cli-connect-timeout 10 \
      --payload "${LAMBDA_PAYLOAD}" \
      "${LAMBDA_RESPONSE_FILE}"
  )"

  python3 - "${INVOKE_OUTPUT}" "${LAMBDA_RESPONSE_FILE}" "${TRADING_DATE}" <<'PY'
import json
import sys

invoke = json.loads(sys.argv[1])
response_path = sys.argv[2]
expected_date = sys.argv[3]

if invoke.get("FunctionError"):
    raise SystemExit(f"Lambda returned FunctionError: {invoke['FunctionError']}")

with open(response_path, "r", encoding="utf-8") as file:
    payload = json.load(file)

if payload.get("statusCode") != 200:
    raise SystemExit(f"Expected Lambda statusCode 200, got {payload.get('statusCode')}: {payload}")

body = json.loads(payload["body"])
required = {"date", "ticker", "percent_change", "close_price"}
missing = required - body.keys()
if missing:
    raise SystemExit(f"Lambda response missing fields: {sorted(missing)}")

if body["date"] != expected_date:
    raise SystemExit(f"Expected Lambda winner date {expected_date}, got {body['date']}")
PY

  rm -f "${LAMBDA_RESPONSE_FILE}"
  pass "Ingestion Lambda stored winner for ${TRADING_DATE}"
fi

echo "Checking API endpoint..."
API_RESPONSE="$(curl --fail --silent --show-error --max-time 20 "${API_URL}")"

python3 - "${API_RESPONSE}" "${TRADING_DATE}" "${RUN_INGESTION}" <<'PY'
import json
import sys

items = json.loads(sys.argv[1])
expected_date = sys.argv[2]
check_ingested_date = sys.argv[3] == "true"

if not isinstance(items, list):
    raise SystemExit("API response is not a JSON array")

if len(items) > 7:
    raise SystemExit(f"API returned more than 7 records: {len(items)}")

required = {"date", "ticker", "percent_change", "close_price"}
for index, item in enumerate(items):
    missing = required - item.keys()
    if missing:
        raise SystemExit(f"API item {index} missing fields: {sorted(missing)}")

if check_ingested_date and expected_date not in {item["date"] for item in items}:
    raise SystemExit(f"API response does not include ingested date {expected_date}")
PY

pass "API Gateway returns valid recent winners JSON"

echo "Checking frontend website..."
FRONTEND_HTML="$(curl --fail --silent --show-error --max-time 20 "${FRONTEND_URL}")"

python3 - "${FRONTEND_HTML}" <<'PY'
import sys

html = sys.argv[1]
required_snippets = [
    "<div id=\"root\"></div>",
    "Daily Stock Top Movers",
]

for snippet in required_snippets:
    if snippet not in html:
        raise SystemExit(f"Frontend HTML missing expected snippet: {snippet}")
PY

pass "S3 static website serves the frontend"
echo "Integration smoke test passed."
