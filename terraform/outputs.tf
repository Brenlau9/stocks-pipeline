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

output "eventbridge_rule_name" {
  value = aws_cloudwatch_event_rule.daily_ingestion_schedule.name
}

output "api_gateway_url" {
  value = aws_apigatewayv2_api.stocks_api.api_endpoint
}

output "movers_endpoint_url" {
  value = "${aws_apigatewayv2_api.stocks_api.api_endpoint}/movers"
}
