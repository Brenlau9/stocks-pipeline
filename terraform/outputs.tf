output "dynamodb_table_name" {
  value = aws_dynamodb_table.daily_stock_movers.name
}

output "dynamodb_table_arn" {
  value = aws_dynamodb_table.daily_stock_movers.arn
}

output "ingestion_lambda_name" {
  value = aws_lambda_function.ingestion_lambda.function_name
}

output "ingestion_lambda_arn" {
  value = aws_lambda_function.ingestion_lambda.arn
}

output "api_lambda_name" {
  value = aws_lambda_function.api_lambda.function_name
}

output "api_lambda_arn" {
  value = aws_lambda_function.api_lambda.arn
}