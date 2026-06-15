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

data "aws_ssm_parameter" "massive_api_key" {
  name            = var.massive_api_key_parameter_name
  with_decryption = false
}

resource "aws_iam_role" "ingestion_lambda_role" {
  name = "stocks-ingestion-lambda-role"

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

resource "aws_iam_role" "api_lambda_role" {
  name = "stocks-api-lambda-role"

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

resource "aws_iam_role_policy" "ingestion_lambda_policy" {
  name = "stocks-ingestion-lambda-policy"
  role = aws_iam_role.ingestion_lambda_role.id

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
          "dynamodb:PutItem"
        ]
        Resource = aws_dynamodb_table.daily_stock_movers.arn
      },
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameter"
        ]
        Resource = data.aws_ssm_parameter.massive_api_key.arn
      }
    ]
  })
}

resource "aws_iam_role_policy" "api_lambda_policy" {
  name = "stocks-api-lambda-policy"
  role = aws_iam_role.api_lambda_role.id

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
          "dynamodb:Scan"
        ]
        Resource = aws_dynamodb_table.daily_stock_movers.arn
      }
    ]
  })
}

resource "aws_lambda_function" "ingestion_lambda" {
  function_name = "stocks-ingestion-lambda"
  role          = aws_iam_role.ingestion_lambda_role.arn
  handler       = "ingestion.handler.lambda_handler"
  runtime       = "python3.12"

  filename         = data.archive_file.ingestion_lambda_zip.output_path
  source_code_hash = data.archive_file.ingestion_lambda_zip.output_base64sha256

  timeout = 300

  environment {
    variables = {
      MASSIVE_API_KEY_PARAMETER_NAME = var.massive_api_key_parameter_name
      DYNAMODB_TABLE_NAME            = aws_dynamodb_table.daily_stock_movers.name
    }
  }
}

resource "aws_lambda_function" "api_lambda" {
  function_name = "stocks-api-lambda"
  role          = aws_iam_role.api_lambda_role.arn
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
