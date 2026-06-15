data "archive_file" "ingestion_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/ingestion_package"
  output_path = "${path.module}/build/ingestion_lambda.zip"
}

data "archive_file" "api_lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/build/api_package"
  output_path = "${path.module}/build/api_lambda.zip"
}

resource "aws_iam_role" "lambda_role" {
  name = "stocks-pipeline-lambda-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "lambda.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "lambda_policy" {
  name = "stocks-pipeline-lambda-policy"
  role = aws_iam_role.lambda_role.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "*"
      },
      {
        Effect = "Allow"
        Action = [
          "dynamodb:PutItem",
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.daily_stock_movers.arn
      }
    ]
  })
}

resource "aws_lambda_function" "ingestion_lambda" {
  function_name = "stocks-ingestion-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "ingestion.handler.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.ingestion_lambda_zip.output_path
  source_code_hash = data.archive_file.ingestion_lambda_zip.output_base64sha256

  timeout = 300

  environment {
    variables = {
      MASSIVE_API_KEY     = var.massive_api_key
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.daily_stock_movers.name
    }
  }
}

resource "aws_lambda_function" "api_lambda" {
  function_name = "stocks-api-lambda"
  role          = aws_iam_role.lambda_role.arn
  handler       = "api.handler.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.api_lambda_zip.output_path
  source_code_hash = data.archive_file.api_lambda_zip.output_base64sha256

  timeout = 30

  environment {
    variables = {
      DYNAMODB_TABLE_NAME = aws_dynamodb_table.daily_stock_movers.name
    }
  }
}