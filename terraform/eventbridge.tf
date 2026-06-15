resource "aws_cloudwatch_event_rule" "daily_ingestion_schedule" {
  name                = "stocks-daily-ingestion-schedule"
  description         = "Runs the stock ingestion Lambda once per day"
  schedule_expression = "cron(0 22 * * ? *)"

  tags = {
    Project = "stocks-pipeline"
  }
}

resource "aws_cloudwatch_event_target" "ingestion_lambda_target" {
  rule      = aws_cloudwatch_event_rule.daily_ingestion_schedule.name
  target_id = "stocks-ingestion-lambda"
  arn       = aws_lambda_function.ingestion_lambda.arn
}

resource "aws_lambda_permission" "allow_eventbridge_ingestion" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.ingestion_lambda.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.daily_ingestion_schedule.arn
}