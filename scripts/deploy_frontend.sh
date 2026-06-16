#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="${ROOT_DIR}/frontend"
TERRAFORM_DIR="${ROOT_DIR}/terraform"
AWS_REGION="${AWS_REGION:-us-west-2}"

echo "Building frontend..."
npm --prefix "${FRONTEND_DIR}" run build

BUCKET_NAME="$(terraform -chdir="${TERRAFORM_DIR}" output -raw frontend_bucket_name)"

echo "Deploying frontend to s3://${BUCKET_NAME}/..."
aws s3 sync "${FRONTEND_DIR}/dist/" "s3://${BUCKET_NAME}/" \
  --delete \
  --region "${AWS_REGION}"

echo "Frontend deployed."
echo "Website URL:"
terraform -chdir="${TERRAFORM_DIR}" output -raw frontend_website_url
echo
