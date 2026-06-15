#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LAMBDA_DIR="${ROOT_DIR}/lambdas"
BUILD_DIR="${ROOT_DIR}/terraform/build"
PYTHON_BIN="${PYTHON_BIN:-python3}"

package_lambda() {
  local name="$1"
  local package_dir="${BUILD_DIR}/${name}_package"
  local source_dir="${LAMBDA_DIR}/${name}"
  local requirements_file="${source_dir}/requirements.txt"

  echo "Packaging ${name} Lambda..."

  rm -rf "${package_dir}"
  mkdir -p "${package_dir}/${name}" "${package_dir}/shared"

  cp -R "${source_dir}/." "${package_dir}/${name}/"
  cp -R "${LAMBDA_DIR}/shared/." "${package_dir}/shared/"

  find "${package_dir}" -type d -name "__pycache__" -prune -exec rm -rf {} +
  find "${package_dir}" -type f -name "*.pyc" -delete

  if [[ -s "${requirements_file}" ]]; then
    "${PYTHON_BIN}" -m pip install \
      --platform manylinux2014_x86_64 \
      --implementation cp \
      --python-version 3.12 \
      --only-binary=:all: \
      --upgrade \
      --target "${package_dir}" \
      -r "${requirements_file}"
  fi
}

mkdir -p "${BUILD_DIR}"

package_lambda "ingestion"
package_lambda "api"

rm -f "${BUILD_DIR}/ingestion_lambda.zip" "${BUILD_DIR}/api_lambda.zip"

echo "Lambda packages rebuilt in ${BUILD_DIR}."
echo "Run: terraform -chdir=terraform apply"
